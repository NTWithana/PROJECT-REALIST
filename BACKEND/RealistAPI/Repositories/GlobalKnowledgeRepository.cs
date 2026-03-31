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
            var filter = Builders<GlobalKnowledge>.Filter.Empty;

            if (!string.IsNullOrWhiteSpace(domain))
                filter &= Builders<GlobalKnowledge>.Filter.Eq(x => x.Domain, domain);

            if (tags != null && tags.Count > 0)
                filter &= Builders<GlobalKnowledge>.Filter.AnyIn(x => x.Tags, tags);

            var candidates = await _collection.Find(filter).ToListAsync();
            if (!candidates.Any()) return candidates;

            static double Cosine(List<double> a, List<double> b)
            {
                double dot = 0, na = 0, nb = 0;
                for (int i = 0; i < a.Count; i++)
                {
                    dot += a[i] * b[i];
                    na += a[i] * a[i];
                    nb += b[i] * b[i];
                }
                return (na == 0 || nb == 0) ? 0.0 : dot / (Math.Sqrt(na) * Math.Sqrt(nb));
            }

            // DYNAMIC WEIGHTS
            static double AdaptiveScore(GlobalKnowledge x, double similarity)
            {
                double reuseWeight = 0.35 + Math.Min(x.ReusedCount / 50.0, 0.25);
                double approvalWeight = 0.25;
                double confidenceWeight = 0.20;
                double freshnessWeight = 0.10;
                double similarityWeight = 1.0 - (reuseWeight + approvalWeight + confidenceWeight + freshnessWeight);

                double quality =
                    Math.Log(1 + x.ReusedCount) * 2.5 +
                    Math.Log(1 + x.ApprovedCount) * 2.0 +
                    Math.Log(1 + x.OptimizedCount) * 1.5;

                double confidence = x.Confidence ?? 0.5;

                var days = (DateTime.UtcNow - x.CreatedAt).TotalDays;
                double freshness = Math.Exp(-days / 30.0);

                return
                    (similarity * similarityWeight) +
                    (quality * reuseWeight / 10.0) +
                    (confidence * confidenceWeight) +
                    (freshness * freshnessWeight);
            }

            return candidates
                .Where(x => x.Embedding != null && x.Embedding.Count == embedding.Count)
                .Select(x => new
                {
                    Item = x,
                    Similarity = Cosine(embedding, x.Embedding)
                })
                .Select(x => new
                {
                    x.Item,
                    Score = AdaptiveScore(x.Item, x.Similarity)
                })
                .OrderByDescending(x => x.Score)
                .Take(limit)
                .Select(x => x.Item)
                .ToList();
        }

        public async Task IncrementApprovedAsync(string id)
        {
            await _collection.UpdateOneAsync(
                x => x.Id == id,
                Builders<GlobalKnowledge>.Update.Inc(x => x.ApprovedCount, 1));
        }

        public async Task IncrementOptimizedAsync(string id)
        {
            await _collection.UpdateOneAsync(
                x => x.Id == id,
                Builders<GlobalKnowledge>.Update.Inc(x => x.OptimizedCount, 1));
        }

        //  BULK REUSE (KEY FEATURE)
        public async Task IncrementReusedBulkAsync(List<string> ids)
        {
            if (ids == null || ids.Count == 0) return;

            var filter = Builders<GlobalKnowledge>.Filter.In(x => x.Id, ids);

            await _collection.UpdateManyAsync(
                filter,
                Builders<GlobalKnowledge>.Update.Inc(x => x.ReusedCount, 1));
        }

        public async Task<List<GlobalKnowledge>> GetTrendingAsync(int limit = 20)
        {
            return await _collection.Find(_ => true)
                .SortByDescending(x => x.ReusedCount + x.ApprovedCount * 2)
                .Limit(limit)
                .ToListAsync();
        }

        public async Task<object> GetStatsAsync()
        {
            var total = await _collection.CountDocumentsAsync(_ => true);
            var reused = await _collection.CountDocumentsAsync(x => x.ReusedCount > 0);

            return new
            {
                total,
                reused
            };
        }
    }
}