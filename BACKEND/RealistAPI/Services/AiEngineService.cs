using System.Net.Http.Json;
using Microsoft.Extensions.Configuration;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Services
{
    public class AiEngineService : IAiEngineService
    {
        private readonly HttpClient _http;
        private readonly string _baseUrl;

        public AiEngineService(HttpClient http, IConfiguration config)
        {
            _http = http;
            _baseUrl = config["AI_ENGINE_URL"]
                       ?? throw new InvalidOperationException("AI_ENGINE_URL not configured");
        }

        //  RUN FULL PIPELINE 
        public async Task<AiEngineResponseDto> RunPipelineAsync(ProblemReqDto req)
        {
            var res = await _http.PostAsJsonAsync($"{_baseUrl}/run-pipeline", req);

            if (!res.IsSuccessStatusCode)
                throw new Exception("AI engine error: " + await res.Content.ReadAsStringAsync());

            var data = await res.Content.ReadFromJsonAsync<AiEngineResponseDto>();
            return data!;
        }

        //  GENERAL CHAT 
        public async Task<string> RunChatAsync(string message)
        {
            var payload = new { message };

            var res = await _http.PostAsJsonAsync($"{_baseUrl}/chat", payload);

            if (!res.IsSuccessStatusCode)
                throw new Exception("AI chat error: " + await res.Content.ReadAsStringAsync());

            var data = await res.Content.ReadFromJsonAsync<ChatResponseDto>();
            return data?.Response ?? "";
        }
    }

    public class ChatResponseDto
    {
        public string Response { get; set; } = "";
    }
}
