using RealistAPI.Models;

namespace RealistAPI.Interfaces
{
    public interface IGlobalKnowledgeRepository
    {
        Task CreateAsync(GlobalKnowledge doc);
        Task<List<GlobalKnowledge>> FindSemanticSimilarAsync(
        List<double> embedding,
        int limit = 10,
        string? domain = null,
        List<string>? tags = null);
        Task IncrementApprovedAsync(string problemId);
        Task IncrementOptimizedAsync(string problemId);
        Task IncrementReusedAsync(string problemId);
        Task<List<GlobalKnowledge>> GetTrendingAsync(int limit = 20);
        Task<object> GetStatsAsync();


    }
}
