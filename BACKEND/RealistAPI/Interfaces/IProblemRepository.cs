using RealistAPI.Models;

namespace RealistAPI.Interfaces
{
    public interface IProblemRepository
    {
        Task<ProblemDocument?> GetByIdAsync(string id);
        Task<List<ProblemDocument>> GetBySessionAsync(string sessionId);
        Task CreateAsync(ProblemDocument problem);
        Task UpdateAsync(ProblemDocument problem);
        Task<List<ProblemDocument>> FindSimilarAsync(string domain, List<string> tags, int limit = 10); // Find similar problems based on domain and tags

    }
}