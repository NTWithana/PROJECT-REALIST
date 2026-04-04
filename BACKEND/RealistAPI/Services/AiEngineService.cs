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

        // RUN FULL PIPELINE
        
        public async Task<AiEngineResponseDto> RunPipelineAsync(ProblemReqDto req)
        {
            Console.WriteLine("Calling AI Engine...");

            var res = await _http.PostAsJsonAsync($"{_baseUrl}/run-pipeline", req);

            // HANDLE ERROR 
            if (!res.IsSuccessStatusCode)
            {
                var err = await res.Content.ReadAsStringAsync();
                Console.WriteLine("AI ERROR RESPONSE:");
                Console.WriteLine(err);

                throw new Exception("AI engine error: " + err);
            }

            // LOG RAW RESPONSE 
            var raw = await res.Content.ReadAsStringAsync();
            Console.WriteLine("RAW AI RESPONSE:");
            Console.WriteLine(raw);

            // SAFE DESERIALIZATION
            var data = JsonSerializer.Deserialize<AiEngineResponseDto>(
                raw,
                new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

            if (data == null)
                throw new Exception("AI returned null or invalid response");

            Console.WriteLine("AI call successful");

            return data;
        }

        // 
        // GENERAL CHAT
        // 
        public async Task<AiChatResponseDto> RunChatAsync(string message)
        {
            var res = await _http.PostAsJsonAsync($"{_baseUrl}/chat", new
            {
                message = message,
                mode = "hub"
            });

            if (!res.IsSuccessStatusCode)
            {
                var err = await res.Content.ReadAsStringAsync();
                Console.WriteLine("AI CHAT ERROR:");
                Console.WriteLine(err);

                throw new Exception("AI chat error: " + err);
            }

            var json = await res.Content.ReadAsStringAsync();

            Console.WriteLine("RAW CHAT RESPONSE:");
            Console.WriteLine(json);

            var result = JsonSerializer.Deserialize<AiChatResponseDto>(
                json,
                new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                });

            if (result == null)
                throw new Exception("AI chat deserialization failed");

            return result;
        }
    }
}