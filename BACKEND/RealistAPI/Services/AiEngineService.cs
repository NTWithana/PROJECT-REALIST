using Microsoft.Extensions.Configuration;
using RealistAPI.Interfaces;
using RealistAPI.Models;
using System.Net.Http.Json;
using System.Text.Json;

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
            if (data == null)
                throw new Exception("AI returned null response");

            return data;
        }

        //  GENERAL CHAT 
        public async Task<AiChatResponseDto> RunChatAsync(string message)
        {
            var res = await _http.PostAsJsonAsync($"{_baseUrl}/chat", new
            {
                message = message,
                mode = "hub"
            });

            res.EnsureSuccessStatusCode();

            var json = await res.Content.ReadAsStringAsync();

            return JsonSerializer.Deserialize<AiChatResponseDto>(
                json,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
            );
        }

    }


}
