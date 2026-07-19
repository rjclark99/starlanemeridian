using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Konscious.Security.Cryptography;
using KodiSetup.Admin.Security;

namespace KodiSetup.Admin.Services;

public sealed class CredentialVault : IDisposable
{
    private sealed record Envelope(int Version, string Salt, string WrappedKey, string Nonce, string Tag, string Ciphertext);
    private readonly SemaphoreSlim gate = new(1, 1);
    private readonly string path;
    private readonly TimeSpan autoLock;
    private readonly Timer timer;
    private byte[]? dataKey;
    private VaultDocument? document;
    private DateTimeOffset lastAccess;
    private int failedAttempts;
    private DateTimeOffset blockedUntil;
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web) { WriteIndented = false };

    public CredentialVault(IConfiguration configuration)
    {
        var configuredPath = configuration["Vault:Path"];
        var root = configuredPath is null
            ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "KodiSetupAdmin")
            : Path.GetDirectoryName(Path.GetFullPath(configuredPath)) ?? throw new ArgumentException("Vault path must include a directory");
        Directory.CreateDirectory(root);
        path = configuredPath is null ? Path.Combine(root, "households.vault") : Path.GetFullPath(configuredPath);
        autoLock = TimeSpan.FromMinutes(configuration.GetValue("Vault:AutoLockMinutes", 15));
        timer = new Timer(_ => CheckAutoLock(), null, TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(1));
    }

    public bool Exists => File.Exists(path);
    public bool IsUnlocked => dataKey is not null && document is not null;

    public async Task CreateAsync(string password)
    {
        ValidatePassword(password);
        await gate.WaitAsync();
        try
        {
            if (Exists) throw new InvalidOperationException("Vault already exists");
            dataKey = RandomNumberGenerator.GetBytes(32);
            document = new VaultDocument([], [new AuditEntry(DateTimeOffset.UtcNow, "vault.created", null, "Encrypted local vault created")]);
            lastAccess = DateTimeOffset.UtcNow;
            await SaveAsync(password, RandomNumberGenerator.GetBytes(16));
        }
        finally { gate.Release(); }
    }

    public async Task UnlockAsync(string password)
    {
        if (DateTimeOffset.UtcNow < blockedUntil) throw new InvalidOperationException("Vault unlock is temporarily throttled");
        await gate.WaitAsync();
        try
        {
            var envelope = JsonSerializer.Deserialize<Envelope>(await File.ReadAllTextAsync(path), JsonOptions) ?? throw new InvalidDataException("Invalid vault envelope");
            if (envelope.Version != 1) throw new InvalidDataException("Unsupported vault version");
            var salt = Convert.FromBase64String(envelope.Salt);
            var passwordKey = await DeriveAsync(password, salt);
            try
            {
                var wrapped = Dpapi.Unprotect(Convert.FromBase64String(envelope.WrappedKey));
                dataKey = DecryptKey(wrapped, passwordKey);
                document = JsonSerializer.Deserialize<VaultDocument>(Decrypt(Convert.FromBase64String(envelope.Ciphertext), dataKey, Convert.FromBase64String(envelope.Nonce), Convert.FromBase64String(envelope.Tag)), JsonOptions)
                    ?? throw new InvalidDataException("Vault content is empty");
                failedAttempts = 0;
                lastAccess = DateTimeOffset.UtcNow;
            }
            catch
            {
                CryptographicOperations.ZeroMemory(passwordKey);
                failedAttempts++;
                blockedUntil = DateTimeOffset.UtcNow.AddSeconds(Math.Min(300, Math.Pow(2, failedAttempts)));
                LockUnsafe();
                throw new UnauthorizedAccessException("Vault password is invalid or this is not the original Windows profile");
            }
            CryptographicOperations.ZeroMemory(passwordKey);
        }
        finally { gate.Release(); }
    }

    public IReadOnlyList<Household> List()
    {
        Touch();
        return RequireDocument().Households.Select(Redact).OrderBy(item => item.DisplayName).ToList();
    }

    public Household? GetSecret(Guid id)
    {
        Touch();
        return RequireDocument().Households.SingleOrDefault(item => item.Id == id);
    }

    public async Task<Household> UpsertAsync(Guid? id, HouseholdInput input)
    {
        ValidateInput(input);
        await gate.WaitAsync();
        try
        {
            Touch();
            var current = id is null ? null : RequireDocument().Households.SingleOrDefault(item => item.Id == id);
            var now = DateTimeOffset.UtcNow;
            var item = new Household(current?.Id ?? Guid.NewGuid(), input.DisplayName.Trim(), EmptyToNull(input.ProtonUsername), EmptyToNull(input.ProtonPassword), EmptyToNull(input.RealDebridUsername), EmptyToNull(input.RealDebridPassword), input.RecordConsent ? current?.ConsentAt ?? now : current?.ConsentAt, input.RecordHandoff ? current?.HandoffAt ?? now : current?.HandoffAt, current?.CreatedAt ?? now, now);
            if (current is not null) RequireDocument().Households.Remove(current);
            RequireDocument().Households.Add(item);
            RequireDocument().Audit.Add(new AuditEntry(now, current is null ? "household.created" : "household.updated", item.Id, "Credential record changed"));
            await PersistUnlockedAsync();
            return Redact(item);
        }
        finally { gate.Release(); }
    }

    public async Task DeleteAsync(Guid id)
    {
        await gate.WaitAsync();
        try
        {
            Touch();
            var item = RequireDocument().Households.SingleOrDefault(value => value.Id == id) ?? throw new KeyNotFoundException();
            RequireDocument().Households.Remove(item);
            RequireDocument().Audit.Add(new AuditEntry(DateTimeOffset.UtcNow, "household.deleted", id, "Credential record permanently removed"));
            await PersistUnlockedAsync();
        }
        finally { gate.Release(); }
    }

    public IReadOnlyList<AuditEntry> Audit()
    {
        Touch();
        return RequireDocument().Audit.OrderByDescending(item => item.At).Take(500).ToList();
    }

    public byte[] ExportEncrypted()
    {
        Touch();
        return File.ReadAllBytes(path);
    }

    public void Lock() { gate.Wait(); try { LockUnsafe(); } finally { gate.Release(); } }

    private async Task PersistUnlockedAsync()
    {
        var envelope = JsonSerializer.Deserialize<Envelope>(await File.ReadAllTextAsync(path), JsonOptions) ?? throw new InvalidDataException();
        var plaintext = JsonSerializer.SerializeToUtf8Bytes(RequireDocument(), JsonOptions);
        var (ciphertext, nonce, tag) = Encrypt(plaintext, dataKey!);
        var updated = envelope with { Nonce = Convert.ToBase64String(nonce), Tag = Convert.ToBase64String(tag), Ciphertext = Convert.ToBase64String(ciphertext) };
        await AtomicWriteAsync(JsonSerializer.Serialize(updated, JsonOptions));
        CryptographicOperations.ZeroMemory(plaintext);
    }

    private async Task SaveAsync(string password, byte[] salt)
    {
        var passwordKey = await DeriveAsync(password, salt);
        var wrapped = Dpapi.Protect(EncryptKey(dataKey!, passwordKey));
        var plaintext = JsonSerializer.SerializeToUtf8Bytes(RequireDocument(), JsonOptions);
        var (ciphertext, nonce, tag) = Encrypt(plaintext, dataKey!);
        var envelope = new Envelope(1, Convert.ToBase64String(salt), Convert.ToBase64String(wrapped), Convert.ToBase64String(nonce), Convert.ToBase64String(tag), Convert.ToBase64String(ciphertext));
        await AtomicWriteAsync(JsonSerializer.Serialize(envelope, JsonOptions));
        CryptographicOperations.ZeroMemory(passwordKey); CryptographicOperations.ZeroMemory(plaintext);
    }

    private async Task AtomicWriteAsync(string value)
    {
        var temporary = path + ".new";
        await File.WriteAllTextAsync(temporary, value, Encoding.UTF8);
        File.Move(temporary, path, true);
    }

    private static async Task<byte[]> DeriveAsync(string password, byte[] salt)
    {
        using var argon = new Argon2id(Encoding.UTF8.GetBytes(password)) { Salt = salt, DegreeOfParallelism = Math.Max(1, Math.Min(4, Environment.ProcessorCount)), Iterations = 3, MemorySize = 65536 };
        return await argon.GetBytesAsync(32);
    }

    private static byte[] EncryptKey(byte[] key, byte[] kek)
    {
        var (ciphertext, nonce, tag) = Encrypt(key, kek);
        return nonce.Concat(tag).Concat(ciphertext).ToArray();
    }

    private static byte[] DecryptKey(byte[] wrapped, byte[] kek) => Decrypt(wrapped[28..], kek, wrapped[..12], wrapped[12..28]);
    private static (byte[] Ciphertext, byte[] Nonce, byte[] Tag) Encrypt(byte[] plaintext, byte[] key) { var nonce = RandomNumberGenerator.GetBytes(12); var tag = new byte[16]; var ciphertext = new byte[plaintext.Length]; using var aes = new AesGcm(key, 16); aes.Encrypt(nonce, plaintext, ciphertext, tag); return (ciphertext, nonce, tag); }
    private static byte[] Decrypt(byte[] ciphertext, byte[] key, byte[] nonce, byte[] tag) { var plaintext = new byte[ciphertext.Length]; using var aes = new AesGcm(key, 16); aes.Decrypt(nonce, ciphertext, tag, plaintext); return plaintext; }
    private VaultDocument RequireDocument() => document ?? throw new InvalidOperationException("Vault is locked");
    private void Touch() { if (!IsUnlocked) throw new InvalidOperationException("Vault is locked"); lastAccess = DateTimeOffset.UtcNow; }
    private void CheckAutoLock() { if (IsUnlocked && DateTimeOffset.UtcNow - lastAccess >= autoLock) Lock(); }
    private void LockUnsafe() { if (dataKey is not null) CryptographicOperations.ZeroMemory(dataKey); dataKey = null; document = null; }
    private static Household Redact(Household value) => value with { ProtonPassword = value.ProtonPassword is null ? null : "••••••••", RealDebridPassword = value.RealDebridPassword is null ? null : "••••••••" };
    private static string? EmptyToNull(string? value) => string.IsNullOrWhiteSpace(value) ? null : value;
    private static void ValidatePassword(string password) { if (password.Length < 14) throw new ArgumentException("Master password must contain at least 14 characters"); }
    private static void ValidateInput(HouseholdInput value) { if (string.IsNullOrWhiteSpace(value.DisplayName) || value.DisplayName.Length > 80) throw new ArgumentException("Display name is required and limited to 80 characters"); foreach (var secret in new[] { value.ProtonPassword, value.RealDebridPassword }) if (secret?.Length > 512) throw new ArgumentException("Credential value is too long"); }
    public void Dispose() { timer.Dispose(); Lock(); gate.Dispose(); }
}
