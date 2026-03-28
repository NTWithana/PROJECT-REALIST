using RealistAPI.Interfaces;
using RealistAPI.Models;
using System.Net.Http.Json;
using static FeedbackDto;

namespace RealistAPI.Services
{
    public class AiEngineService : IAiEngineService
    {
        private readonly HttpClient _http;
        private readonly string _aiUrl;

        public AiEngineService(HttpClient http, IConfiguration config)
        {
            _http = http;
            _aiUrl = config["AI_ENGINE_URL"] ?? "http://localhost:8000";
        }

        // Run full PESO pipeline
        public async Task<AiEngineResponseDto> RunPipelineAsync(ProblemReqDto req)
        {
            var response = await _http.PostAsJsonAsync($"{_aiUrl}/run-pipeline", req);

            if (!response.IsSuccessStatusCode)
                throw new Exception("AI engine error: " + await response.Content.ReadAsStringAsync());

            var result = await response.Content.ReadFromJsonAsync<AiEngineResponseDto>();
            return result!;
        }

        // General Chat AI
        public async Task<string> RunChatAsync(string message)
        {
            var payload = new { message = message };

            var response = await _http.PostAsJsonAsync($"{_aiUrl}/chat", payload);

            if (!response.IsSuccessStatusCode)
                throw new Exception("AI chat error: " + await response.Content.ReadAsStringAsync());

            // Try JSON first
            try
            {
                var json = await response.Content.ReadFromJsonAsync<ChatResponseDto>();
                if (json != null && !string.IsNullOrWhiteSpace(json.Message))
                    return json.Message;
            }
            catch
            {
                // Ignore JSON parsing errors
            }

            // Fallback: raw text
            return await response.Content.ReadAsStringAsync();
        }
    }
}