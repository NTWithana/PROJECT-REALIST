using MongoDB.Driver;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Repositories
{
    public class GlobalKnowledgeRepository : IGlobalKnowledgeRepository
    {
        private readonly IMongoCollection<GlobalKnowledge> _collection;

        public GlobalKnowledgeRepository(IMongoDatabase db)
        {
            _collection = db.GetCollection<GlobalKnowledge>("GlobalKnowledge");
        }

        public async Task CreateAsync(GlobalKnowledge doc)
        {
            await _collection.InsertOneAsync(doc);
        }

        public async Task<List<GlobalKnowledge>> FindSemanticSimilarAsync(
    List<double> embedding,
    int limit = 10,
    string? domain = null,
    List<string>? tags = null)
        {
            if (embedding == null || embedding.Count == 0)
                return new List<GlobalKnowledge>();

            // 1) Build a filter to reduce candidate set
            var filter = Builders<GlobalKnowledge>.Filter.Empty;

            if (!string.IsNullOrWhiteSpace(domain))
            {
                filter &= Builders<GlobalKnowledge>.Filter.Eq(x => x.Domain, domain);
            }

            if (tags != null && tags.Count > 0)
            {
                filter &= Builders<GlobalKnowledge>.Filter.AnyIn(x => x.Tags, tags);
            }

            // Optional: only last N days to keep it fresh
            // var cutoff = DateTime.UtcNow.AddDays(-90);
            // filter &= Builders<GlobalKnowledge>.Filter.Gte(x => x.CreatedAt, cutoff);

            var candidates = await _collection.Find(filter).ToListAsync();

            if (!candidates.Any())
                return candidates;

            static double Cosine(List<double> a, List<double> b)
            {
                if (a == null || b == null || a.Count != b.Count) return 0.0;

                double dot = 0, na = 0, nb = 0;
                for (int i = 0; i < a.Count; i++)
                {
                    dot += a[i] * b[i];
                    na += a[i] * a[i];
                    nb += b[i] * b[i];
                }
                if (na == 0 || nb == 0) return 0.0;
                return dot / (Math.Sqrt(na) * Math.Sqrt(nb));
            }

            return candidates
                .Where(x => x.Embedding != null && x.Embedding.Count == embedding.Count)
                .OrderByDescending(x => Cosine(embedding, x.Embedding))
                .Take(limit)
                .ToList();
        }
        public async Task IncrementApprovedAsync(string problemId)
        {
            var filter = Builders<GlobalKnowledge>.Filter.Eq(x => x.ProblemId, problemId);
            var update = Builders<GlobalKnowledge>.Update.Inc(x => x.ApprovedCount, 1);
            await _collection.UpdateManyAsync(filter, update);
        }

        public async Task IncrementOptimizedAsync(string problemId)
        {
            var filter = Builders<GlobalKnowledge>.Filter.Eq(x => x.ProblemId, problemId);
            var update = Builders<GlobalKnowledge>.Update.Inc(x => x.OptimizedCount, 1);
            await _collection.UpdateManyAsync(filter, update);
        }

        public async Task IncrementReusedAsync(string problemId)
        {
            var filter = Builders<GlobalKnowledge>.Filter.Eq(x => x.ProblemId, problemId);
            var update = Builders<GlobalKnowledge>.Update.Inc(x => x.ReusedCount, 1);
            await _collection.UpdateManyAsync(filter, update);
        }
        public async Task<List<GlobalKnowledge>> GetTrendingAsync(int limit = 20)
        {
            var all = await _collection.Find(Builders<GlobalKnowledge>.Filter.Empty).ToListAsync();

            return all
                .OrderByDescending(x =>
                    (x.ReusedCount * 3) +
                    (x.ApprovedCount * 2) +
                    (x.OptimizedCount * 1) +
                    (x.Confidence ?? 0))
                .Take(limit)
                .ToList();
        }
        public async Task<object> GetStatsAsync()
        {
            var all = await _collection.Find(Builders<GlobalKnowledge>.Filter.Empty).ToListAsync();

            var total = all.Count;

            var byDomain = all
                .GroupBy(x => x.Domain ?? "unknown")
                .Select(g => new { domain = g.Key, count = g.Count() })
                .ToList();

            var topTags = all
                .SelectMany(x => x.Tags ?? new List<string>())
                .GroupBy(t => t)
                .OrderByDescending(g => g.Count())
                .Take(20)
                .Select(g => new { tag = g.Key, count = g.Count() })
                .ToList();

            return new
            {
                totalEntries = total,
                byDomain,
                topTags
            };
        }

    }
}
