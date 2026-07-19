using System.IO.Compression;
using System.Text;
using KodiSetup.Admin;
using KodiSetup.Admin.Services;
using Microsoft.Extensions.Configuration;

var failures = new List<string>();
void Check(bool condition, string message) { if (!condition) failures.Add(message); }
void Throws<T>(Action action, string message) where T : Exception
{
    try { action(); failures.Add(message); } catch (T) { }
}

Check(AdbService.NormalizeAddress("192.168.1.64") == "192.168.1.64:5555", "Default ADB port was not applied");
Check(AdbService.NormalizeAddress("fire-tv.local:4444") == "fire-tv.local:4444", "Valid hostname/port was rejected");
foreach (var address in new[] { "", " 192.168.1.64", "192.168.1.999", "fire tv", "-firetv", "firetv-", "firetv:0", "firetv:65536", "firetv;whoami", "a:b:c" })
    Throws<ArgumentException>(() => AdbService.NormalizeAddress(address), $"Unsafe address was accepted: {address}");

Check(ControlApiClient.IsSupportedCommand("SYNC_CONFIG"), "Allowlisted command was rejected");
Check(!ControlApiClient.IsSupportedCommand("SHELL"), "Arbitrary command was accepted");
Check(PasswordGenerator.Password().Length == 24, "Generated password length is incorrect");
Check(PasswordGenerator.Password(1).Length == 18, "Generated password minimum was not enforced");
Check(PasswordGenerator.UsernameSuggestion().StartsWith("home-", StringComparison.Ordinal), "Username prefix is incorrect");

var root = Path.Combine(Path.GetTempPath(), "starlane-admin-tests-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(root);
try
{
    string CreateZip(string name, params (string Path, string Content)[] entries)
    {
        var path = Path.Combine(root, name);
        using var archive = ZipFile.Open(path, ZipArchiveMode.Create);
        foreach (var item in entries)
        {
            var entry = archive.CreateEntry(item.Path);
            using var writer = new StreamWriter(entry.Open(), Encoding.UTF8);
            writer.Write(item.Content);
        }
        return path;
    }

    var valid = CreateZip("valid.zip", ("repository.kodisetup/addon.xml", "<addon id=\"repository.kodisetup\" version=\"1.0.2\" />"), ("repository.kodisetup/service.py", "pass"));
    var extracted = Path.Combine(root, "valid-output");
    AdbService.ValidateAndExtractBootstrap(valid, extracted);
    Check(File.Exists(Path.Combine(extracted, "repository.kodisetup", "addon.xml")), "Valid bootstrap was not extracted");
    var traversal = CreateZip("traversal.zip", ("repository.kodisetup/addon.xml", "<addon id=\"repository.kodisetup\" />"), ("repository.kodisetup/../escape.txt", "bad"));
    Throws<ArgumentException>(() => AdbService.ValidateAndExtractBootstrap(traversal, Path.Combine(root, "traversal-output")), "Traversal ZIP was accepted");
    var wrongId = CreateZip("wrong-id.zip", ("repository.kodisetup/addon.xml", "<addon id=\"repository.attacker\" />"));
    Throws<ArgumentException>(() => AdbService.ValidateAndExtractBootstrap(wrongId, Path.Combine(root, "wrong-output")), "Wrong add-on ID was accepted");
    var wrongRoot = CreateZip("wrong-root.zip", ("repository.kodisetup/addon.xml", "<addon id=\"repository.kodisetup\" />"), ("other/file.txt", "bad"));
    Throws<ArgumentException>(() => AdbService.ValidateAndExtractBootstrap(wrongRoot, Path.Combine(root, "root-output")), "Unexpected ZIP root was accepted");

    var vaultPath = Path.Combine(root, "vault", "households.vault");
    var configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?> { ["Vault:Path"] = vaultPath, ["Vault:AutoLockMinutes"] = "15" }).Build();
    const string password = "correct horse battery staple";
    Guid householdId;
    await using (var holder = new AsyncDisposableVault(new CredentialVault(configuration)))
    {
        Throws<ArgumentException>(() => holder.Vault.CreateAsync("too-short").GetAwaiter().GetResult(), "Short master password was accepted");
        await holder.Vault.CreateAsync(password);
        var saved = await holder.Vault.UpsertAsync(null, new HouseholdInput("Test Home", "proton-user", "proton-secret", "debrid-user", "debrid-secret", true, true));
        householdId = saved.Id;
        Check(saved.ProtonPassword != "proton-secret" && saved.RealDebridPassword != "debrid-secret", "Returned household was not redacted");
        Check(holder.Vault.GetSecret(householdId)?.ProtonPassword == "proton-secret", "Unlocked vault did not retain the secret");
        var encrypted = holder.Vault.ExportEncrypted();
        Check(!Encoding.UTF8.GetString(encrypted).Contains("proton-secret", StringComparison.Ordinal), "Vault export contains plaintext credentials");
        holder.Vault.Lock();
        Throws<InvalidOperationException>(() => holder.Vault.List(), "Locked vault returned records");
    }
    await using (var holder = new AsyncDisposableVault(new CredentialVault(configuration)))
    {
        await holder.Vault.UnlockAsync(password);
        Check(holder.Vault.GetSecret(householdId)?.RealDebridPassword == "debrid-secret", "Vault did not decrypt after restart");
        await holder.Vault.DeleteAsync(householdId);
        Check(holder.Vault.List().Count == 0, "Vault deletion did not remove the household");
    }
    await using (var holder = new AsyncDisposableVault(new CredentialVault(configuration)))
        await ThrowsAsync<UnauthorizedAccessException>(() => holder.Vault.UnlockAsync("definitely wrong"), "Wrong vault password was accepted");
}
finally
{
    if (Directory.Exists(root) && Path.GetFullPath(root).StartsWith(Path.GetFullPath(Path.GetTempPath()), StringComparison.OrdinalIgnoreCase)) Directory.Delete(root, true);
}

if (failures.Count > 0)
{
    Console.Error.WriteLine(string.Join(Environment.NewLine, failures));
    return 1;
}
Console.WriteLine("Windows administration tests passed");
return 0;

async Task ThrowsAsync<T>(Func<Task> action, string message) where T : Exception
{
    try { await action(); failures.Add(message); } catch (T) { }
}

sealed class AsyncDisposableVault(CredentialVault vault) : IAsyncDisposable
{
    public CredentialVault Vault { get; } = vault;
    public ValueTask DisposeAsync() { Vault.Dispose(); return ValueTask.CompletedTask; }
}
