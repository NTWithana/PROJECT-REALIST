using MongoDB.Driver;
using RealistAPI.Models;

namespace RealistAPI.Interfaces
{
    public interface ISessionRepository
    {
        Task<CollaborationSession?> GetByIdAsync(string id);
        Task CreateAsync(CollaborationSession session);
        Task UpdateAsync(CollaborationSession session);
        Task AddCollaboratorAsync(string sessionId, string userId);

        Task<List<CollaborationSession>> GetAllAsync();
    }


}