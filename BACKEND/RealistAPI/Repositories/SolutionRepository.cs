using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Options;
using MongoDB.Driver;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Repositories
{
    public class SolutionRepository : ISolutionRepository
    {
        private readonly IMongoCollection<SolutionDocument> _solutions;

        public SolutionRepository(IMongoClient client, IOptions<MongoDbSetget> settings)
        {
            var db = client.GetDatabase(settings.Value.DBName);
            _solutions = db.GetCollection<SolutionDocument>("Solutions");
        }

        public async Task<SolutionDocument?> GetByIdAsync(string id) =>
            await _solutions.Find(s => s.Id == id).FirstOrDefaultAsync();

        public async Task CreateAsync(SolutionDocument doc) =>
            await _solutions.InsertOneAsync(doc);

        public async Task UpdateAsync(SolutionDocument doc) =>
            await _solutions.ReplaceOneAsync(s => s.Id == doc.Id, doc);
        



    }
}