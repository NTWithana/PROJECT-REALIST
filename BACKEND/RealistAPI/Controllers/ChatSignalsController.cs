using Microsoft.AspNetCore.Mvc;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Controllers
{
    [ApiController]
    [Route("api/chat-signals")]
    public class ChatSignalsController : ControllerBase
    {
        private readonly IChatSignalRepository _repo;
        private readonly IEmbeddingService _embedding;

        public ChatSignalsController(
            IChatSignalRepository repo,
            IEmbeddingService embedding)
        {
            _repo = repo;
            _embedding = embedding;
        }

        
        // WRITE: EVOLUTION
      
        [HttpPost]
        public async Task<IActionResult> Ingest([FromBody] ChatSignal signal)
        {
            if (string.IsNullOrWhiteSpace(signal.Pattern))
                return BadRequest("Pattern required");

            await _repo.CreateAsync(signal);
            return Ok();
        }

        // READ: SEMANTIC MEMORY
  
        [HttpGet("semantic-similar")]
        public async Task<IActionResult> GetSimilar(
            [FromQuery] string query,
            [FromQuery] string? domain,
            [FromQuery] List<string>? tags)
        {
            if (string.IsNullOrWhiteSpace(query))
                return BadRequest("Query is required");

            var embedding = _embedding.GenerateEmbedding(query);

            var results = await _repo.FindSemanticSimilarAsync(
                embedding,
                limit: 10,
                domain: domain,
                tags: tags
            );

            var shaped = results.Select(x => new
            {
                id = x.Id,
                category = x.Category,
                pattern = x.Pattern,
                importance = x.Importance,
                created_at = x.CreatedAt
            });

            return Ok(shaped);
        }
    }
}
