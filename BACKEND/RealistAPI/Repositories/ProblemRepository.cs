using Microsoft.Extensions.Options;
using MongoDB.Driver;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Repositories
{
    public class ProblemRepository : IProblemRepository
    {
        private readonly IMongoCollection<ProblemDocument> _problems;

        public ProblemRepository(IMongoClient client, IOptions<MongoDbSetget> settings)
        {
            var db = client.GetDatabase(settings.Value.DBName);
            _problems = db.GetCollection<ProblemDocument>("Problems");
        }
        public async Task<List<ProblemDocument>> FindSimilarAsync(string domain, List<string> tags, int limit = 10) // This method finds similar problems based on domain and tags
        {
            var filter = Builders<ProblemDocument>.Filter.And(
                Builders<ProblemDocument>.Filter.Eq(p => p.Domain, domain),
                Builders<ProblemDocument>.Filter.AnyIn(p => p.Tags, tags)
            );

            return await _problems
                .Find(filter)
                .Limit(limit)
                .ToListAsync();
        }

        public async Task<ProblemDocument?> GetByIdAsync(string id) =>
            await _problems.Find(p => p.Id == id).FirstOrDefaultAsync();

        public async Task<List<ProblemDocument>> GetBySessionAsync(string sessionId) =>
            await _problems.Find(p => p.SessionId == sessionId).ToListAsync();

        public async Task CreateAsync(ProblemDocument problem) =>
            await _problems.InsertOneAsync(problem);

        public async Task UpdateAsync(ProblemDocument problem) =>
            await _problems.ReplaceOneAsync(p => p.Id == problem.Id, problem);
    }
}
