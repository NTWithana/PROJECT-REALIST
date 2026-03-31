using MongoDB.Driver;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Repositories
{
    public class ChatSignalRepository : IChatSignalRepository
    {
        private readonly IMongoCollection<ChatSignal> _collection;

        public ChatSignalRepository(IMongoDatabase db)
        {
            _collection = db.GetCollection<ChatSignal>("ChatSignals");
        }

        public async Task CreateAsync(ChatSignal signal)
        {
            await _collection.InsertOneAsync(signal);
        }

        public async Task<List<ChatSignal>> FindSemanticSimilarAsync(
            List<double> embedding,
            int limit = 10,
            string? domain = null,
            List<string>? tags = null)
        {
            var filter = Builders<ChatSignal>.Filter.Empty;

            if (!string.IsNullOrWhiteSpace(domain))
                filter &= Builders<ChatSignal>.Filter.Eq(x => x.Domain, domain);

            if (tags != null && tags.Count > 0)
                filter &= Builders<ChatSignal>.Filter.AnyIn(x => x.Tags, tags);

            // v1: recency + importance ranking
            return await _collection
                .Find(filter)
                .SortByDescending(x => x.Importance)
                .ThenByDescending(x => x.CreatedAt)
                .Limit(limit)
                .ToListAsync();
        }
    }
}
