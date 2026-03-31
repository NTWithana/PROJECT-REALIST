using RealistAPI.Models;

public interface IChatSignalRepository
{
    Task CreateAsync(ChatSignal signal);
    Task<List<ChatSignal>> FindSemanticSimilarAsync(
        List<double> embedding,
        int limit = 10,
        string? domain = null,
        List<string>? tags = null);
}
