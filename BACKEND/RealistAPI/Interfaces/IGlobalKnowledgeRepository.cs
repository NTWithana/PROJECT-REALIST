using RealistAPI.Models;

namespace RealistAPI.Interfaces
{
    public interface IGlobalKnowledgeRepository
    {
        Task<GlobalKnowledge> CreateAsync(GlobalKnowledge doc);

        Task<List<GlobalKnowledge>> FindSemanticSimilarAsync(
            List<double> embedding,
            int limit = 10,
            string? domain = null,
            List<string>? tags = null);

        Task IncrementApprovedAsync(string knowledgeId);
        Task IncrementOptimizedAsync(string knowledgeId);

        //  AUTO-REUSE SUPPORT
        Task IncrementReusedBulkAsync(List<string> knowledgeIds);

        // OPTIONAL ANALYTICS
        Task<List<GlobalKnowledge>> GetTrendingAsync(int limit = 20);
        Task<object> GetStatsAsync();
    }
}