using RealistAPI.Models;

namespace RealistAPI.Interfaces
{
    public interface IUserRepository
    {
        Task<User?> GetByEmailAsync(string email);
        Task<User?> GetByIdAsync(string id);
        Task CreateAsync(User user);
    }
}
