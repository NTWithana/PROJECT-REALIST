using System.Threading.Tasks;
using RealistAPI.Models;

namespace RealistAPI.Interfaces
{
    public interface IAiEngineService
    {
        Task<AiEngineResponseDto> RunPipelineAsync(ProblemReqDto req);
        Task<string> RunChatAsync(string message);
    }
}
