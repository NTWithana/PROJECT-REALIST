using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using RealistAPI.Interfaces;
using RealistAPI.Models;
using System.Security.Claims;

using static FeedbackDto;

namespace RealistAPI.Controllers
{
    [ApiController]
    [Route("api/sessions/{sessionId}/problems")]
    [Authorize]
    public class ProblemController : ControllerBase
    {
        private readonly ISessionRepository _sessions;
        private readonly IProblemRepository _problems;
        private readonly ISolutionRepository _solutions;
        private readonly IAiEngineService _ai;
        private readonly IGlobalKnowledgeRepository _globalKnowledge;
        private readonly IEmbeddingService _embedding;

        public ProblemController(
            ISessionRepository sessions,
            IProblemRepository problems,
            ISolutionRepository solutions,
            IAiEngineService ai,
            IGlobalKnowledgeRepository globalKnowledge,
            IEmbeddingService embedding)
        {
            _sessions = sessions;
            _problems = problems;
            _solutions = solutions;
            _ai = ai;
            _globalKnowledge = globalKnowledge;
            _embedding = embedding;
        }

        private string? GetUserId() =>
                   User.FindFirst(ClaimTypes.NameIdentifier)?.Value;


        private bool IsLeader(CollaborationSession session, string userId) =>
            session.LeaderId == userId;

        // GLOBAL RAG ENDPOINT
       

        [HttpGet("/api/knowledge/semantic-similar")]
        [AllowAnonymous]
        public async Task<IActionResult> GetSemanticSimilar(
            [FromQuery] string query,
            [FromQuery] string? domain,
            [FromQuery] List<string>? tags)
        {
            if (string.IsNullOrWhiteSpace(query))
                return BadRequest("Query is required");

            var embedding = _embedding.GenerateEmbedding(query);

            var results = await _globalKnowledge.FindSemanticSimilarAsync(
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

        // RUN AI
        

        [HttpPost("{problemId}/run-ai")]
        [Authorize]
        public async Task<IActionResult> RunAiForProblem(string sessionId, string problemId)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsLeader(session, userId))
                return Forbid("Only leader can run AI");

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Invalid problem");

            var req = new ProblemReqDto
            {
                SessionId = sessionId,
                Description = problem.Description,
                Suggestions = problem.Suggestions,
                Domain = problem.Domain,
                Tags = problem.Tags
            };

            var aiResult = await _ai.RunPipelineAsync(req);
            if (aiResult == null)
                return StatusCode(500, "AI returned null response");

            if (aiResult.OptimisedSolution == null)
                return StatusCode(500, "AI failed to generate solution");

            if (string.IsNullOrWhiteSpace(aiResult.OptimisedSolution))
                return StatusCode(500, "AI returned empty solution");

            var reuseIds = aiResult.RetrievedKnowledgeIds?
                .Where(x => !string.IsNullOrWhiteSpace(x))
                .Distinct()
                .ToList() ?? new List<string>();

            if (reuseIds?.Any() == true)
                await _globalKnowledge.IncrementReusedBulkAsync(reuseIds);

            SolutionDocument solutionDoc;

            if (problem.SolutionDocumentId == null)
            {
                solutionDoc = new SolutionDocument
                {
                    ProblemId = problem.Id,
                    Versions = new List<SolutionVersion>()
                };

                await _solutions.CreateAsync(solutionDoc);
                problem.SolutionDocumentId = solutionDoc.Id;
                await _problems.UpdateAsync(problem);
            }
            else
            {
                solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);
            }

            if (solutionDoc == null)
                return StatusCode(500, "Solution document error");
            
            var version = new SolutionVersion
            {
                Id = Guid.NewGuid().ToString(),
                SolutionText = aiResult.OptimisedSolution ?? "",
                Critique = aiResult.Critique ?? "",
                Improvements = aiResult.Improvements ?? "",
                Iteration = solutionDoc.Versions.Count + 1,
                Confidence = aiResult.Confidence ?? 0.0,
                Created_At = aiResult.Created_At ?? DateTime.UtcNow,

                DeepCore = aiResult.DeepCore ?? "",
                UsedRag = aiResult.UsedRag ?? false,
                UsedDeep = aiResult.UsedDeep ?? false,
                DeepCacheHit = aiResult.DeepCacheHit ?? false,
                RagCacheHit = aiResult.RagCacheHit ?? false,
                ProblemKey = aiResult.ProblemKey ?? "",

                RetrievedKnowledgeIds = reuseIds ?? new List<string>()
            };

            solutionDoc.Versions.Add(version);
            await _solutions.UpdateAsync(solutionDoc);

            var embedding = _embedding.GenerateEmbedding(version.SolutionText);

            var knowledge = new GlobalKnowledge
            {
                ProblemId = problem.Id,
                SessionId = sessionId,
                Domain = problem.Domain,
                Tags = problem.Tags ?? new List<string>(),

                ProblemKey = aiResult.ProblemKey ?? "",
                ProblemSummary = problem.Description,
                SolutionSummary = version.SolutionText,
                DeepCore = aiResult.DeepCore ?? "",

                SourceKnowledgeIds = reuseIds ?? new List<string>(),
                UsedRag = aiResult.UsedRag ?? false,
                UsedDeep = aiResult.UsedDeep ?? false,
                DeepCacheHit = aiResult.DeepCacheHit ?? false,
                RagCacheHit = aiResult.RagCacheHit ?? false,

                Confidence = version.Confidence,
                CreatedAt = DateTime.UtcNow,
                Embedding = embedding,
                Score = 0
            };

            await _globalKnowledge.CreateAsync(knowledge);

            return Ok(version);
        }


     
        // APPROVE AI
    

        [HttpPost("{problemId}/approve-ai")]
        public async Task<IActionResult> ApproveAiSuggestion(
            string sessionId,
            string problemId,
            [FromBody] ApproveAiRequest req)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null) return NotFound();

            var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);

            if (solutionDoc == null)
                return BadRequest("Solution document missing");

            var version = new SolutionVersion
            {
                Id = Guid.NewGuid().ToString(),
                SolutionText = req.MergedText,
                Critique = "AI suggestion approved",
                Improvements = req.SuggestionSummary,
                Iteration = solutionDoc.Versions.Count + 1,
                Confidence = 1.0,
                Created_At = DateTime.UtcNow
            };

            solutionDoc.Versions.Add(version);
            await _solutions.UpdateAsync(solutionDoc);

            var embedding = _embedding.GenerateEmbedding(version.SolutionText);

            var knowledge = new GlobalKnowledge
            {
                ProblemId = problem.Id,
                SessionId = sessionId,
                Domain = problem.Domain,
                Tags = problem.Tags ?? new List<string>(),

                ProblemSummary = problem.Description,
                SolutionSummary = version.SolutionText,
                Confidence = 1.0,
                CreatedAt = DateTime.UtcNow,

                Embedding = embedding,
                SourceKnowledgeIds = new List<string>(),

                UsedRag = false,
                UsedDeep = false,
                DeepCacheHit = false,
                RagCacheHit = false,
                Score = 0
            };

            await _globalKnowledge.CreateAsync(knowledge);
            await _globalKnowledge.IncrementApprovedAsync(knowledge.Id);

            return Ok(version);
        }

        // OPTIMIZE

        [HttpPost("{problemId}/optimize")]
        public async Task<IActionResult> OptimizeSolution(
            string sessionId,
            string problemId,
            [FromBody] FeedbackDto feedback)
        {
            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null) return NotFound();

            var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);
            var currentVersion = solutionDoc?.Versions.LastOrDefault();

            if (currentVersion == null)
                return BadRequest("No existing solution");

            var aiReq = new ProblemReqDto
            {
                SessionId = sessionId,
                Description = currentVersion.SolutionText,
                Suggestions = string.Join("\n", feedback.Messages),
                Domain = problem.Domain,
                Tags = problem.Tags
            };

            var aiResult = await _ai.RunPipelineAsync(aiReq);
            if (aiResult == null)
                return StatusCode(500, "AI returned null response");

            if (aiResult.OptimisedSolution == null)
                return StatusCode(500, "AI failed to generate solution");

            if (string.IsNullOrWhiteSpace(aiResult.OptimisedSolution))
                return StatusCode(500, "AI returned empty solution");

            var reuseIds = aiResult.RetrievedKnowledgeIds?
                .Where(x => !string.IsNullOrWhiteSpace(x))
                .Distinct()
                .ToList() ?? new List<string>();

            if (reuseIds?.Any() == true)
                await _globalKnowledge.IncrementReusedBulkAsync(reuseIds);

            var newVersion = new SolutionVersion
            {
                Id = Guid.NewGuid().ToString(),
                SolutionText = aiResult.OptimisedSolution ?? "",
                Critique = aiResult.Critique ?? "",
                Improvements = aiResult.Improvements ?? "",
                Iteration = solutionDoc.Versions.Count + 1,
                Confidence = aiResult.Confidence ?? 0.0,
                Created_At = aiResult.Created_At ?? DateTime.UtcNow,

                DeepCore = aiResult.DeepCore ?? "",
                UsedRag = aiResult.UsedRag ?? false,
                UsedDeep = aiResult.UsedDeep ?? false,
                DeepCacheHit = aiResult.DeepCacheHit ?? false,
                RagCacheHit = aiResult.RagCacheHit ?? false,
                ProblemKey = aiResult.ProblemKey ?? "",

                RetrievedKnowledgeIds = reuseIds ?? new List<string>()
            };

            solutionDoc.Versions.Add(newVersion);
            await _solutions.UpdateAsync(solutionDoc);

            var embedding = _embedding.GenerateEmbedding(newVersion.SolutionText);

            var knowledge = new GlobalKnowledge
            {
                ProblemId = problem.Id,
                SessionId = sessionId,
                Domain = problem.Domain,
                Tags = problem.Tags ?? new List<string>(),

                ProblemKey = aiResult.ProblemKey ?? "",
                ProblemSummary = problem.Description,
                SolutionSummary = newVersion.SolutionText,
                DeepCore = aiResult.DeepCore ?? "",

                SourceKnowledgeIds = reuseIds ?? new List<string>(),
                UsedRag = aiResult.UsedRag ?? false,
                UsedDeep = aiResult.UsedDeep ?? false,
                DeepCacheHit = aiResult.DeepCacheHit ?? false,
                RagCacheHit = aiResult.RagCacheHit ?? false,

                Confidence = newVersion.Confidence,
                CreatedAt = DateTime.UtcNow,
                Embedding = embedding,
                Score = 0
            };

            await _globalKnowledge.CreateAsync(knowledge);
            await _globalKnowledge.IncrementOptimizedAsync(knowledge.Id);

            return Ok(newVersion);
        }
    }
}