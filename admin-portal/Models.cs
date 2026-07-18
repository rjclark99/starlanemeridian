namespace KodiSetup.Admin;

public sealed record Household(
    Guid Id,
    string DisplayName,
    string? ProtonUsername,
    string? ProtonPassword,
    string? RealDebridUsername,
    string? RealDebridPassword,
    DateTimeOffset? ConsentAt,
    DateTimeOffset? HandoffAt,
    DateTimeOffset CreatedAt,
    DateTimeOffset UpdatedAt);

public sealed record AuditEntry(DateTimeOffset At, string Action, Guid? HouseholdId, string Detail);
public sealed record VaultDocument(List<Household> Households, List<AuditEntry> Audit);
public sealed record VaultPassword(string Password);
public sealed record HouseholdInput(string DisplayName, string? ProtonUsername, string? ProtonPassword, string? RealDebridUsername, string? RealDebridPassword, bool RecordConsent, bool RecordHandoff);
public sealed record AdbRequest(string DeviceAddress, string? ApkPath, string? BootstrapPath);
public sealed record PairingCodeRequest(string HouseholdAlias);
