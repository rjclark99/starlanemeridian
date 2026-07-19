using System.Diagnostics;
using System.IO.Compression;
using System.Net;
using System.Text.RegularExpressions;
using System.Xml.Linq;

namespace KodiSetup.Admin.Services;

public sealed partial class AdbService
{
    private readonly string executable;
    public AdbService(IConfiguration configuration) => executable = configuration["AdbPath"] ?? "adb.exe";

    public Task<string> Devices(CancellationToken cancellation) => Run(["devices", "-l"], cancellation);
    public Task<string> Connect(string address, CancellationToken cancellation)
    {
        return Run(["connect", NormalizeAddress(address)], cancellation);
    }
    public Task<string> Install(string address, string apkPath, CancellationToken cancellation)
    {
        if (!File.Exists(apkPath) || !apkPath.EndsWith(".apk", StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("APK path is invalid");
        return Run(["-s", NormalizeAddress(address), "install", "-r", apkPath], cancellation);
    }

    public async Task<string> DeployBootstrap(string address, string zipPath, CancellationToken cancellation)
    {
        if (!File.Exists(zipPath) || !zipPath.EndsWith(".zip", StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("Bootstrap ZIP path is invalid");
        var serial = NormalizeAddress(address);
        const string addons = "/sdcard/Android/data/org.xbmc.kodi/files/.kodi/addons";
        const string probe = addons + "/.kodisetup_probe";
        var temporary = Path.Combine(Path.GetTempPath(), "kodi-setup-" + Guid.NewGuid().ToString("N"));
        try
        {
            ValidateAndExtractBootstrap(zipPath, temporary);
            try
            {
                await Run(["-s", serial, "shell", "mkdir", "-p", addons], cancellation);
                await Run(["-s", serial, "shell", "touch", probe], cancellation);
                await Run(["-s", serial, "shell", "rm", "-f", probe], cancellation);
                var output = await Run(["-s", serial, "push", Path.Combine(temporary, "repository.kodisetup"), addons + "/"], cancellation);
                return "Direct bootstrap deployment succeeded. Start Kodi; the service add-on will run automatically.\n" + output;
            }
            catch (InvalidOperationException)
            {
                var output = await Run(["-s", serial, "push", zipPath, "/sdcard/Download/repository.kodisetup.zip"], cancellation);
                return "Kodi's external add-on directory is not writable. Guided ZIP fallback copied repository.kodisetup.zip to Downloads.\n" + output;
            }
        }
        finally
        {
            if (Directory.Exists(temporary) && Path.GetFullPath(temporary).StartsWith(Path.GetFullPath(Path.GetTempPath()), StringComparison.OrdinalIgnoreCase)) Directory.Delete(temporary, true);
        }
    }

    internal static string NormalizeAddress(string address)
    {
        if (string.IsNullOrWhiteSpace(address) || address != address.Trim() || address.Count(character => character == ':') > 1)
            throw new ArgumentException("Use an IPv4/hostname and optional port only");
        var separator = address.LastIndexOf(':');
        var host = separator < 0 ? address : address[..separator];
        var portText = separator < 0 ? "5555" : address[(separator + 1)..];
        if (!int.TryParse(portText, out var port) || port is < 1 or > 65535)
            throw new ArgumentException("Device port must be between 1 and 65535");
        var numericLooking = host.All(character => char.IsDigit(character) || character == '.');
        if ((numericLooking && (!IPAddress.TryParse(host, out var ip) || ip.AddressFamily != System.Net.Sockets.AddressFamily.InterNetwork)) ||
            (!numericLooking && !HostnamePattern().IsMatch(host)))
            throw new ArgumentException("Use a valid IPv4 address or DNS hostname");
        return $"{host}:{port}";
    }

    internal static void ValidateAndExtractBootstrap(string zipPath, string destination)
    {
        using var archive = ZipFile.OpenRead(zipPath);
        if (archive.Entries.Count > 512 || archive.Entries.Sum(entry => entry.Length) > 25L * 1024 * 1024)
            throw new ArgumentException("Bootstrap ZIP is too large");
        if (!archive.Entries.Any(entry => entry.FullName.Replace('\\', '/').Equals("repository.kodisetup/addon.xml", StringComparison.Ordinal)))
            throw new ArgumentException("ZIP must contain repository.kodisetup/addon.xml");
        foreach (var entry in archive.Entries)
        {
            var name = entry.FullName.Replace('\\', '/');
            if (name.StartsWith('/') || name.Split('/').Any(part => part == "..") || (!string.IsNullOrEmpty(name) && !name.StartsWith("repository.kodisetup/", StringComparison.Ordinal)))
                throw new ArgumentException("Bootstrap ZIP contains an unsafe or unexpected path");
        }
        var addonEntry = archive.GetEntry("repository.kodisetup/addon.xml")!;
        using (var stream = addonEntry.Open())
        {
            var addon = XDocument.Load(stream, LoadOptions.None).Root;
            if (addon?.Name.LocalName != "addon" || addon.Attribute("id")?.Value != "repository.kodisetup")
                throw new ArgumentException("Bootstrap addon.xml ID is invalid");
        }
        Directory.CreateDirectory(destination);
        archive.ExtractToDirectory(destination);
    }

    private async Task<string> Run(IEnumerable<string> arguments, CancellationToken cancellation)
    {
        var start = new ProcessStartInfo(executable) { UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true, CreateNoWindow = true };
        foreach (var argument in arguments) start.ArgumentList.Add(argument);
        using var process = Process.Start(start) ?? throw new InvalidOperationException("ADB could not start. Configure AdbPath in appsettings.json.");
        var output = process.StandardOutput.ReadToEndAsync(cancellation); var error = process.StandardError.ReadToEndAsync(cancellation);
        await process.WaitForExitAsync(cancellation);
        var result = (await output) + (await error);
        if (process.ExitCode != 0) throw new InvalidOperationException(result.Trim());
        return result.Trim();
    }

    [GeneratedRegex("^(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$")]
    private static partial Regex HostnamePattern();
}
