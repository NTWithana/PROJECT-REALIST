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
        public async Task<GlobalKnowledge> CreateAsync(GlobalKnowledge doc)
        {
            await _collection.InsertOneAsync(doc);
            return doc;
        }


        public async Task<List<GlobalKnowledge>> FindSemanticSimilarAsync(
    List<double> embedding,
    int limit = 10,
    string? domain = null,
    List<string>? tags = null)
        {
            if (embedding == null || embedding.Count == 0)
                return new List<GlobalKnowledge>();

            var filter = Builders<GlobalKnowledge>.Filter.Empty;

            if (!string.IsNullOrWhiteSpace(domain))
                filter &= Builders<GlobalKnowledge>.Filter.Eq(x => x.Domain, domain);

            if (tags != null && tags.Count > 0)
                filter &= Builders<GlobalKnowledge>.Filter.AnyIn(x => x.Tags, tags);

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

            static double Quality(GlobalKnowledge x)
            {
                double score =
                    Math.Log(1 + x.ApprovedCount) * 2.0 +
                    Math.Log(1 + x.ReusedCount) * 3.0 +
                    Math.Log(1 + x.OptimizedCount) * 1.0;

                return Math.Min(score / 10.0, 1.0); // normalize 0–1
            }

            static double Freshness(GlobalKnowledge x)
            {
                var days = (DateTime.UtcNow - x.CreatedAt).TotalDays;
                return Math.Exp(-days / 30.0); // 30‑day half‑life
            }

            return candidates
                .Where(x => x.Embedding != null && x.Embedding.Count == embedding.Count)
                .Select(x => new
                {
                    Item = x,
                    Similarity = Cosine(embedding, x.Embedding),
                    Quality = Quality(x),
                    Freshness = Freshness(x)
                })
                .OrderByDescending(x =>
                    (x.Similarity * 0.70) +
                    (x.Quality * 0.20) +
                    (x.Freshness * 0.10))
                .Take(limit)
                .Select(x => x.Item)
                .ToList();
        }

        public async Task IncrementApprovedAsync(string knowledgeId)
        {
            var filter = Builders<GlobalKnowledge>.Filter.Eq(x => x.Id, knowledgeId);
            var update = Builders<GlobalKnowledge>.Update.Inc(x => x.ApprovedCount, 1);
            await _collection.UpdateOneAsync(filter, update);
        }

        public async Task IncrementOptimizedAsync(string knowledgeId)
        {
            var filter = Builders<GlobalKnowledge>.Filter.Eq(x => x.Id, knowledgeId);
            var update = Builders<GlobalKnowledge>.Update.Inc(x => x.OptimizedCount, 1);
            await _collection.UpdateOneAsync(filter, update);
        }

        public async Task IncrementReusedAsync(string knowledgeId)
        {
            var filter = Builders<GlobalKnowledge>.Filter.Eq(x => x.Id, knowledgeId);
            var update = Builders<GlobalKnowledge>.Update.Inc(x => x.ReusedCount, 1);
            await _collection.UpdateOneAsync(filter, update);
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
