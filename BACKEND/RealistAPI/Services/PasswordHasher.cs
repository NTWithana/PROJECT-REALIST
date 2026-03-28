using Konscious.Security.Cryptography;
using System.Security.Cryptography;
using System.Text;

namespace RealistAPI.Services
{
    public interface IPasswordHasher
    {
        string Hash(string password);
        bool Verify(string password, string hash);
    }

    public class Argon2PasswordHasher : IPasswordHasher
    {
        public string Hash(string password)
        {
            // Generate a random salt
            byte[] salt = RandomNumberGenerator.GetBytes(16);

            var argon2 = new Argon2id(Encoding.UTF8.GetBytes(password))
            {
                Salt = salt,
                DegreeOfParallelism = 4, // CPU threads
                Iterations = 4,
                MemorySize = 1024 * 64 // 64 MB
            };

            byte[] hashBytes = argon2.GetBytes(32);

            // Return salt + hash as Base64
            return $"{Convert.ToBase64String(salt)}.{Convert.ToBase64String(hashBytes)}";
        }

        public bool Verify(string password, string storedHash)
        {
            var parts = storedHash.Split('.');
            if (parts.Length != 2)
                return false;

            byte[] salt = Convert.FromBase64String(parts[0]);
            byte[] expectedHash = Convert.FromBase64String(parts[1]);

            var argon2 = new Argon2id(Encoding.UTF8.GetBytes(password))
            {
                Salt = salt,
                DegreeOfParallelism = 4,
                Iterations = 4,
                MemorySize = 1024 * 64
            };

            byte[] actualHash = argon2.GetBytes(32);

            return actualHash.SequenceEqual(expectedHash);
        }
    }
}
