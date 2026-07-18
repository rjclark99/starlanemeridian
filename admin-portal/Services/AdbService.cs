using System.Diagnostics;
using System.IO.Compression;
using System.Text.RegularExpressions;

namespace KodiSetup.Admin.Services;

public sealed partial class AdbService
{
    private readonly string executable;
    public AdbService(IConfiguration configuration) => executable = configuration["AdbPath"] ?? "adb.exe";

    public Task<string> Devices(CancellationToken cancellation) => Run(["devices", "-l"], cancellation);
    public Task<string> Connect(string address, CancellationToken cancellation)
    {
        if (!AddressPattern().IsMatch(address)) throw new ArgumentException("Use an IPv4/hostname and optional port only");
        return Run(["connect", address.Contains(':') ? address : address + ":5555"], cancellation);
    }
    public Task<string> Install(string address, string apkPath, CancellationToken cancellation)
    {
        if (!File.Exists(apkPath) || !apkPath.EndsWith(".apk", StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("APK path is invalid");
        if (!AddressPattern().IsMatch(address)) throw new ArgumentException("Device address is invalid");
        return Run(["-s", address.Contains(':') ? address : address + ":5555", "install", "-r", apkPath], cancellation);
    }

    public async Task<string> DeployBootstrap(string address, string zipPath, CancellationToken cancellation)
    {
        if (!File.Exists(zipPath) || !zipPath.EndsWith(".zip", StringComparison.OrdinalIgnoreCase)) throw new ArgumentException("Bootstrap ZIP path is invalid");
        if (!AddressPattern().IsMatch(address)) throw new ArgumentException("Device address is invalid");
        var serial = address.Contains(':') ? address : address + ":5555";
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

    private static void ValidateAndExtractBootstrap(string zipPath, string destination)
    {
        using var archive = ZipFile.OpenRead(zipPath);
        if (!archive.Entries.Any(entry => entry.FullName.Replace('\\', '/').Equals("repository.kodisetup/addon.xml", StringComparison.Ordinal)))
            throw new ArgumentException("ZIP must contain repository.kodisetup/addon.xml");
        foreach (var entry in archive.Entries)
        {
            var name = entry.FullName.Replace('\\', '/');
            if (name.StartsWith('/') || name.Split('/').Any(part => part == "..") || (!string.IsNullOrEmpty(name) && !name.StartsWith("repository.kodisetup/", StringComparison.Ordinal)))
                throw new ArgumentException("Bootstrap ZIP contains an unsafe or unexpected path");
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

    [GeneratedRegex("^[A-Za-z0-9.-]+(:[0-9]{1,5})?$")] private static partial Regex AddressPattern();
}
