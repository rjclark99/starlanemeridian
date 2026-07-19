using KodiSetup.Admin;
using KodiSetup.Admin.Services;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls(builder.Configuration["Urls"] ?? "http://127.0.0.1:54731");
builder.Services.AddSingleton<CredentialVault>();
builder.Services.AddSingleton<AdbService>();
builder.Services.AddSingleton<ControlApiClient>();
var app = builder.Build();
app.Use(async (context, next) =>
{
    if (!context.Connection.LocalIpAddress!.Equals(System.Net.IPAddress.Loopback) && !context.Connection.LocalIpAddress.Equals(System.Net.IPAddress.IPv6Loopback))
    { context.Response.StatusCode = 403; return; }
    context.Response.Headers.CacheControl = "no-store";
    context.Response.Headers["X-Content-Type-Options"] = "nosniff";
    context.Response.Headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'";
    await next();
});
app.UseDefaultFiles();
app.UseStaticFiles();

app.MapGet("/api/vault/status", (CredentialVault vault) => new { vault.Exists, vault.IsUnlocked });
app.MapPost("/api/vault/create", CreateVault);
app.MapPost("/api/vault/unlock", UnlockVault);
app.MapPost("/api/vault/lock", (CredentialVault vault) => { vault.Lock(); return Results.Ok(); });
app.MapGet("/api/households", (CredentialVault vault) => vault.List());
app.MapGet("/api/households/{id:guid}/secret", (Guid id, CredentialVault vault) => vault.GetSecret(id) is { } item ? Results.Ok(item) : Results.NotFound());
app.MapPost("/api/households", async (HouseholdInput input, CredentialVault vault) => Results.Ok(await vault.UpsertAsync(null, input)));
app.MapPut("/api/households/{id:guid}", async (Guid id, HouseholdInput input, CredentialVault vault) => Results.Ok(await vault.UpsertAsync(id, input)));
app.MapDelete("/api/households/{id:guid}", async (Guid id, CredentialVault vault) => { await vault.DeleteAsync(id); return Results.NoContent(); });
app.MapGet("/api/audit", (CredentialVault vault) => vault.Audit());
app.MapGet("/api/vault/export", (CredentialVault vault) => Results.File(vault.ExportEncrypted(), "application/octet-stream", "kodi-setup-vault-backup.vault"));
app.MapGet("/api/generate", () => new { username = PasswordGenerator.UsernameSuggestion(), password = PasswordGenerator.Password() });
app.MapGet("/api/adb/devices", async (AdbService adb, CancellationToken cancellation) => new { output = await adb.Devices(cancellation) });
app.MapPost("/api/adb/connect", async (AdbRequest input, AdbService adb, CancellationToken cancellation) => new { output = await adb.Connect(input.DeviceAddress, cancellation) });
app.MapPost("/api/adb/install", async (AdbRequest input, AdbService adb, CancellationToken cancellation) => new { output = await adb.Install(input.DeviceAddress, input.ApkPath ?? throw new ArgumentException("APK path is required"), cancellation) });
app.MapPost("/api/adb/bootstrap", async (AdbRequest input, AdbService adb, CancellationToken cancellation) => new { output = await adb.DeployBootstrap(input.DeviceAddress, input.BootstrapPath ?? throw new ArgumentException("Bootstrap ZIP path is required"), cancellation) });
app.MapGet("/api/control/devices", async (ControlApiClient control, CancellationToken cancellation) => await control.Devices(cancellation));
app.MapPost("/api/control/pairing", async (PairingCodeRequest input, ControlApiClient control, CancellationToken cancellation) => await control.CreatePairingCode(input.HouseholdAlias, cancellation));
app.MapPost("/api/control/devices/{id:guid}/commands/{kind}", async (Guid id, string kind, ControlApiClient control, CancellationToken cancellation) => await control.Command(id, kind, cancellation));
app.MapDelete("/api/control/devices/{id:guid}", async (Guid id, ControlApiClient control, CancellationToken cancellation) => { await control.Delete(id, cancellation); return Results.NoContent(); });
app.MapDelete("/api/control/households/{id:guid}", async (Guid id, ControlApiClient control, CancellationToken cancellation) => { await control.DeleteHousehold(id, cancellation); return Results.NoContent(); });

app.Run();

static async Task<IResult> CreateVault(VaultPassword input, CredentialVault vault)
{
    try
    {
        await vault.CreateAsync(input.Password);
        return Results.Ok();
    }
    catch (ArgumentException error)
    {
        return Results.Json(new { error = error.Message }, statusCode: StatusCodes.Status400BadRequest);
    }
    catch (InvalidOperationException error)
    {
        return Results.Json(new { error = error.Message }, statusCode: StatusCodes.Status409Conflict);
    }
}

static async Task<IResult> UnlockVault(VaultPassword input, CredentialVault vault)
{
    try
    {
        await vault.UnlockAsync(input.Password);
        return Results.Ok();
    }
    catch (UnauthorizedAccessException error)
    {
        return Results.Json(new { error = error.Message }, statusCode: StatusCodes.Status401Unauthorized);
    }
    catch (FileNotFoundException)
    {
        return Results.Json(new { error = "No vault exists yet" }, statusCode: StatusCodes.Status404NotFound);
    }
    catch (InvalidOperationException error)
    {
        return Results.Json(new { error = error.Message }, statusCode: StatusCodes.Status429TooManyRequests);
    }
}
