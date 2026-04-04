using Microsoft.AspNetCore.Mvc;
using RealistAPI.Interfaces;
using RealistAPI.Services;

namespace RealistAPI.Controllers
{
    [ApiController]
    [Route("api/hub/assistant")]
    public class HubAssistantController : ControllerBase
    {
        private readonly IAiEngineService _ai;

        public HubAssistantController(IAiEngineService ai)
        {
            _ai = ai;
        }

        public class HubAssistantRequest
        {
            public string Message { get; set; }
        }

        [HttpPost]
        public async Task<IActionResult> AskAssistant([FromBody] HubAssistantRequest req)
        {
            if (string.IsNullOrWhiteSpace(req.Message))
                return BadRequest("Message is required");

            var prompt =
                "You are the Realist Global Hub Assistant. " +
                "Your job is to help users understand global insights, stats, trends, " +
                "and how to use Realist. " +
                "You can reference global knowledge summaries, but never private session data.\n\n" +
                $"User message:\n{req.Message}";

            var response = await _ai.RunChatAsync(prompt);

            return Ok(new
            {
                response = response.Response ?? "",
                meta = new
                {
                    intent = response.Intent ?? "",
                    confidence = response.Confidence,
                    usedRag = response.UsedGlobalRag,
                    usedDeep = response.UsedDeep,
                    retrievedKnowledgeIds = response.RetrievedGlobalKnowledgeIds ?? new List<string>()
                }
            });


        }
    }
}