using Microsoft.AspNetCore.Mvc;
using RealistAPI.Interfaces;
using RealistAPI.Models;

namespace RealistAPI.Controllers
{
    [ApiController]
    [Route("api/knowledge")]
    public class KnowledgeController : ControllerBase
    {
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
    }
}
