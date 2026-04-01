using System.Threading.Tasks;
using RealistAPI.Models;

namespace RealistAPI.Interfaces
{
    public interface IAiEngineService
    {
        Task<AiEngineResponseDto> RunPipelineAsync(ProblemReqDto req);

        //returns structured chat response
        Task<AiChatResponseDto> RunChatAsync(string message);
    }
}
