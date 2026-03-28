using MongoDB.Driver;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Repositories
{
    public class SessionRepository : ISessionRepository
    {
        private readonly IMongoCollection<CollaborationSession> _sessions;

        public SessionRepository(IMongoDatabase db)
        {
            _sessions = db.GetCollection<CollaborationSession>("Sessions");
        }

        public async Task<CollaborationSession> GetByIdAsync(string id) =>
            await _sessions.Find(s => s.Id == id).FirstOrDefaultAsync();

        public async Task CreateAsync(CollaborationSession session) =>
            await _sessions.InsertOneAsync(session);

        public async Task UpdateAsync(CollaborationSession session) =>
            await _sessions.ReplaceOneAsync(s => s.Id == session.Id, session);

        public async Task AddCollaboratorAsync(string sessionId, string userId)
        {
            var update = Builders<CollaborationSession>.Update.AddToSet(s => s.Collaborators, userId);
            await _sessions.UpdateOneAsync(s => s.Id == sessionId, update);
        }
        public async Task<List<CollaborationSession>> GetAllAsync() =>
        await _sessions.Find(_ => true).ToListAsync();



    }

}
