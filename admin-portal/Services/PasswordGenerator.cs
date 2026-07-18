using System.Security.Cryptography;

namespace KodiSetup.Admin.Services;

public static class PasswordGenerator
{
    private const string Alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%+-_";
    private const string Username = "abcdefghjkmnpqrstuvwxyz23456789";
    public static string Password(int length = 24) => Generate(Alphabet, Math.Clamp(length, 18, 64));
    public static string UsernameSuggestion() => "home-" + Generate(Username, 12);
    private static string Generate(string alphabet, int length) => new(Enumerable.Range(0, length).Select(_ => alphabet[RandomNumberGenerator.GetInt32(alphabet.Length)]).ToArray());
}

