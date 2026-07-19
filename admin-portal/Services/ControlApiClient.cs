using System.Net.Http.Json;
using System.Text.Json;

namespace KodiSetup.Admin.Services;

public sealed class ControlApiClient
{
    private static readonly HashSet<string> AllowedCommands =
    [
        "START_SETUP", "INSTALL_KODI", "INSTALL_PROTON", "PREPARE_BOOTSTRAP",
        "OPEN_KODI", "BEGIN_REAL_DEBRID_AUTH", "SYNC_CONFIG",
        "RETRY_CURRENT_STEP", "RETRY_STEP", "OPEN_AUTHORIZATION", "REQUEST_DIAGNOSTICS"
    ];
    private readonly HttpClient client;
    public ControlApiClient(IConfiguration configuration)
    {
        var section = configuration.GetSection("ControlApi");
        client = new HttpClient { BaseAddress = new Uri(section["BaseUrl"] ?? "https://example.invalid"), Timeout = TimeSpan.FromSeconds(20) };
        if (!string.IsNullOrWhiteSpace(section["AccessClientId"])) client.DefaultRequestHeaders.Add("CF-Access-Client-Id", section["AccessClientId"]);
        if (!string.IsNullOrWhiteSpace(section["AccessClientSecret"])) client.DefaultRequestHeaders.Add("CF-Access-Client-Secret", section["AccessClientSecret"]);
    }

    public async Task<JsonElement> Devices(CancellationToken cancellation) => await Get("/v1/admin/devices", cancellation);
    public async Task<JsonElement> CreatePairingCode(string alias, CancellationToken cancellation) => await Post("/v1/admin/pairing-codes", new { householdAlias = alias }, cancellation);
    public async Task<JsonElement> Command(Guid deviceId, string kind, CancellationToken cancellation)
    {
        if (!IsSupportedCommand(kind)) throw new ArgumentException("Unsupported command");
        object payload = kind == "REQUEST_DIAGNOSTICS" ? new { requiresConsent = true, reason = "Administrator requested setup diagnostics" } : new { };
        return await Post($"/v1/admin/devices/{deviceId}/commands", new { kind, payload }, cancellation);
    }
    internal static bool IsSupportedCommand(string kind) => AllowedCommands.Contains(kind);
    public async Task Delete(Guid deviceId, CancellationToken cancellation)
    {
        using var response = await client.DeleteAsync($"/v1/admin/devices/{deviceId}", cancellation);
        await Ensure(response);
    }
    public async Task DeleteHousehold(Guid householdId, CancellationToken cancellation)
    {
        using var response = await client.DeleteAsync($"/v1/admin/households/{householdId}", cancellation);
        await Ensure(response);
    }
    private async Task<JsonElement> Get(string path, CancellationToken cancellation) { using var response = await client.GetAsync(path, cancellation); return await Read(response, cancellation); }
    private async Task<JsonElement> Post(string path, object body, CancellationToken cancellation) { using var response = await client.PostAsJsonAsync(path, body, cancellation); return await Read(response, cancellation); }
    private static async Task<JsonElement> Read(HttpResponseMessage response, CancellationToken cancellation) { await Ensure(response); return (await response.Content.ReadFromJsonAsync<JsonElement>(cancellationToken: cancellation)); }
    private static async Task Ensure(HttpResponseMessage response) { if (!response.IsSuccessStatusCode) throw new InvalidOperationException($"Control API {(int)response.StatusCode}: {await response.Content.ReadAsStringAsync()}"); }
}
