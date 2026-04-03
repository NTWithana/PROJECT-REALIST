using MongoDB.Driver;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Repositories
{
    public class UserRepository : IUserRepository
    {
        private readonly IMongoCollection<User?> _users;

        public UserRepository(IMongoDatabase db)
        {
            _users = db.GetCollection<User?>("Users");
        }

        public async Task<User?> GetByEmailAsync(string email) =>
            await _users.Find(u => u.Email == email).FirstOrDefaultAsync();

        public async Task<User?> GetByIdAsync(string id) =>
            await _users.Find(u => u.Id == id).FirstOrDefaultAsync();

        public async Task CreateAsync(User user) =>
            await _users.InsertOneAsync(user);
    }
}
