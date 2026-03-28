using System.Collections.Generic;
namespace RealistAPI.Interfaces
{
    public interface IEmbeddingService
    {
        List<double> GenerateEmbedding(string text);
    }
}
