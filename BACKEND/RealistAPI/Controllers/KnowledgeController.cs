using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Controllers
{
    [ApiController]
    [Route("api/knowledge")]
    public class KnowledgeController : ControllerBase
    {
        private readonly IEmbeddingService _embedding;
        private readonly IGlobalKnowledgeRepository _global;

        public KnowledgeController(IGlobalKnowledgeRepository global)
        {
            _global = global;
        }

        [HttpGet("trending")]
        public async Task<IActionResult> GetTrending([FromQuery] int limit = 20)
        {
            var items = await _global.GetTrendingAsync(limit);

            var shaped = items.Select(r => new
            {
                problem_summary = r.ProblemSummary,
                solution_summary = r.SolutionSummary,
                domain = r.Domain,
                tags = r.Tags,
                confidence = r.Confidence,
                approved = r.ApprovedCount,
                optimized = r.OptimizedCount,
                reused = r.ReusedCount,
                created_at = r.CreatedAt
            });

            return Ok(shaped);
        }

        [HttpGet("stats")]
        public async Task<IActionResult> GetStats()
        {
            var stats = await _global.GetStatsAsync();
            return Ok(stats);
       
        }

        // GLOBAL RAG ENDPOINT


        [HttpGet("semantic-similar")]
        [AllowAnonymous]
        public async Task<IActionResult> GetSemanticSimilar(
            [FromQuery] string query,
            [FromQuery] string? domain,
            [FromQuery] List<string>? tags)
        {
            if (string.IsNullOrWhiteSpace(query))
                return BadRequest("Query is required");

            var embedding = _embedding.GenerateEmbedding(query);

            var results = await _global.FindSemanticSimilarAsync(
                embedding, 10, domain, tags);

            var shaped = results.Select(r => new
            {
                id = r.Id,
                problem_summary = r.ProblemSummary,
                solution_summary = r.SolutionSummary,
                domain = r.Domain,
                tags = r.Tags,
                confidence = r.Confidence,
                approved_count = r.ApprovedCount,
                optimized_count = r.OptimizedCount,
                reused_count = r.ReusedCount,
                created_at = r.CreatedAt
            });

            return Ok(shaped);
        }

    }
}
