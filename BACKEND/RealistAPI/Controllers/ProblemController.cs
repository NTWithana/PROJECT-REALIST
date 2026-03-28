using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using RealistAPI.Interfaces;
using RealistAPI.Models;

using static FeedbackDto;

namespace RealistAPI.Controllers
{
    [ApiController]
    [Route("api/sessions/{sessionId}/problems")]
    [Authorize] // All endpoints require JWT
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

        // Helper: get userId from JWT
        private string? GetUserId() =>
            User.FindFirst("sub")?.Value;

        // Helper: ensure user is collaborator
        private bool IsCollaborator(CollaborationSession session, string userId) =>
            session.Collaborators.Contains(userId);

        // Helper: ensure user is leader
        private bool IsLeader(CollaborationSession session, string userId) =>
            session.LeaderId == userId;

        //Retrieve similar problems and solutions from global knowledge base (RAG)
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
                embedding,
                10,
                domain,
                tags);

            var shaped = results.Select(r => new
            {
                problem_summary = r.ProblemSummary,
                solution_summary = r.SolutionSummary,
                domain = r.Domain,
                tags = r.Tags,
                confidence = r.Confidence,
                approved_count = r.ApprovedCount,
                optimized_count = r.OptimizedCount,
                reused_count = r.ReusedCount
            });


            return Ok(shaped);
        }


        // CREATE PROBLEM

        [HttpPost]
        public async Task<IActionResult> CreateProblem(
            string sessionId,
            [FromBody] CreateProblemRequest req)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsCollaborator(session, userId))
                return Forbid("You are not a collaborator in this session");

            var problem = new ProblemDocument
            {
                SessionId = sessionId,
                CreatedByUserId = userId,
                Description = req.Description,
                Suggestions = req.Suggestions,
                Domain = req.Domain,
                Tags = req.Tags
            };

            await _problems.CreateAsync(problem);

            if (session.ActiveProblemId == null)
            {
                session.ActiveProblemId = problem.Id;
                await _sessions.UpdateAsync(session);
            }

            return Ok(problem);
        }


        // LIST PROBLEMS

        [HttpGet]
        public async Task<IActionResult> GetProblems(string sessionId)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsCollaborator(session, userId))
                return Forbid();

            var problems = await _problems.GetBySessionAsync(sessionId);
            return Ok(problems);
        }


        // SET ACTIVE PROBLEM (Leader Only)

        [HttpPost("{problemId}/set-active")]
        public async Task<IActionResult> SetActiveProblem(string sessionId, string problemId)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsLeader(session, userId))
                return Forbid("Only the session leader can set the active problem");

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            session.ActiveProblemChanges.Add(new ActiveProblemChange
            {
                ProblemId = problemId,
                ChangedByUserId = userId,
                Timestamp = DateTime.UtcNow
            });

            session.ActiveProblemId = problemId;
            await _sessions.UpdateAsync(session);

            return Ok(new { ActiveProblemId = problemId });
        }

        [HttpGet("similar")] //retriv similar problems and solutions (RAG) 
        public async Task<IActionResult> GetSimilarProblems(
        string sessionId,
        [FromQuery] string domain,
         [FromQuery] List<string> tags)
        {
            var problems = await _problems.FindSimilarAsync(domain, tags, 10);

            var result = problems.Select(p => new
            {
                summary = p.Description,
                solution_summary = p.SolutionDocumentId != null
                    ? "Solution exists" // or fetch best version summary
                    : "No solution yet"
            });

            return Ok(result);
        }

        // RUN AI (Leader Only)

        [HttpPost("{problemId}/run-ai")]
        public async Task<IActionResult> RunAiForProblem(string sessionId, string problemId)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsLeader(session, userId))
                return Forbid("Only the session leader can run AI");

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            var req = new ProblemReqDto
            {
                SessionId = sessionId,
                Description = problem.Description,
                Suggestions = problem.Suggestions,
                Domain = problem.Domain,
                Tags = problem.Tags
            };

            var aiResult = await _ai.RunPipelineAsync(req);

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

            var version = new SolutionVersion
            {
                Id = Guid.NewGuid().ToString(),
                SolutionText = aiResult.OptimisedSolution,
                Critique = aiResult.Critique,
                Improvements = aiResult.Improvements,
                Iteration = solutionDoc.Versions.Count + 1,
                Confidence = aiResult.Confidence,
                Created_At = DateTime.UtcNow
            };

            solutionDoc.Versions.Add(version);
            await _solutions.UpdateAsync(solutionDoc);
            await _globalKnowledge.CreateAsync(new GlobalKnowledge
            {
                ProblemId = problem.Id,
                SessionId = sessionId,
                Domain = problem.Domain,
                Tags = problem.Tags ?? new List<string>(),
                ProblemSummary = problem.Description,
                SolutionSummary = version.SolutionText,
                Confidence = version.Confidence,
                CreatedAt = DateTime.UtcNow
            });


            return Ok(version);
        }

        [HttpPatch("{problemId}/edit")]
        public async Task<IActionResult> EditSolution(
        string sessionId,
        string problemId,
        [FromBody] EditSolutionRequest req)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsCollaborator(session, userId))
                return Forbid("Only collaborators can edit the solution");

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            if (problem.SolutionDocumentId == null)
                return BadRequest("AI has not generated a solution yet");

            var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);

            var version = new SolutionVersion
            {
                Id = Guid.NewGuid().ToString(),
                SolutionText = req.NewText,
                Critique = "Manual edit",
                Improvements = req.Comment,
                Iteration = solutionDoc.Versions.Count + 1,
                Confidence = 1.0,
                Created_At = DateTime.UtcNow
            };

            solutionDoc.Versions.Add(version);
            await _solutions.UpdateAsync(solutionDoc);

            return Ok(version);
        }


        [HttpPost("{problemId}/ask-ai")]
        public async Task<IActionResult> AskAi(
        string sessionId,
        string problemId,
        [FromBody] ChatAiRequest req)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsCollaborator(session, userId))
                return Forbid("Only collaborators can ask AI");

            var aiResponse = await _ai.RunChatAsync(req.Message);

            return Ok(new { response = aiResponse });
        }


        [HttpPost("{problemId}/approve-ai")]
        public async Task<IActionResult> ApproveAiSuggestion(
    string sessionId,
    string problemId,
    [FromBody] ApproveAiRequest req)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsCollaborator(session, userId))
                return Forbid("Only collaborators can approve AI suggestions");

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            if (problem.SolutionDocumentId == null)
                return BadRequest("No solution exists yet");

            var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);

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
            
            await _globalKnowledge.CreateAsync(new GlobalKnowledge
            {
                ProblemId = problem.Id,
                SessionId = sessionId,
                Domain = problem.Domain,
                Tags = problem.Tags ?? new List<string>(),
                ProblemSummary = problem.Description,
                SolutionSummary = req.MergedText,
                Confidence = 1.0,
                CreatedAt = DateTime.UtcNow
            });
            // After creating new GlobalKnowledge entry
            await _globalKnowledge.IncrementApprovedAsync(problem.Id);


            return Ok(version);
        }


        [HttpPost("{problemId}/optimize")]
        public async Task<IActionResult> OptimizeSolution(
        string sessionId,
        string problemId,
        [FromBody] FeedbackDto feedback)
        {
            var userId = GetUserId();
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!IsCollaborator(session, userId))
                return Forbid("Only collaborators can optimize the solution");

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            if (problem.SolutionDocumentId == null)
                return BadRequest("No solution exists yet");

            var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);
            var currentVersion = solutionDoc.Versions.LastOrDefault();

            if (currentVersion == null)
                return BadRequest("No versions exist for this solution");

            // Build AI request using feedback
            var aiReq = new ProblemReqDto
            {
                SessionId = sessionId,
                Description = currentVersion.SolutionText,
                Suggestions = string.Join("\n", feedback.Messages),
                Domain = problem.Domain,
                Tags = problem.Tags
            };

            var aiResult = await _ai.RunPipelineAsync(aiReq);

            var newVersion = new SolutionVersion
            {
                Id = Guid.NewGuid().ToString(),
                SolutionText = aiResult.OptimisedSolution,
                Critique = aiResult.Critique,
                Improvements = aiResult.Improvements,
                Iteration = solutionDoc.Versions.Count + 1,
                Confidence = aiResult.Confidence,
                Created_At = DateTime.UtcNow
            };

            solutionDoc.Versions.Add(newVersion);
            await _solutions.UpdateAsync(solutionDoc);
            
            await _globalKnowledge.CreateAsync(new GlobalKnowledge
            {
                ProblemId = problem.Id,
                SessionId = sessionId,
                Domain = problem.Domain,
                Tags = problem.Tags ?? new List<string>(),
                ProblemSummary = problem.Description,
                SolutionSummary = newVersion.SolutionText,
                Confidence = newVersion.Confidence,
                CreatedAt = DateTime.UtcNow
            });
            await _globalKnowledge.IncrementOptimizedAsync(problem.Id);


            return Ok(newVersion);
        }

        [HttpGet("{problemId}/solution")]
        public async Task<IActionResult> GetLatestSolution(string sessionId, string problemId)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!session.Collaborators.Contains(userId))
                return Forbid();

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            if (problem.SolutionDocumentId == null)
                return Ok(new { message = "No solution yet" });

            var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);
            var latest = solutionDoc.Versions.LastOrDefault();

            return Ok(latest);
        }


        [HttpGet("{problemId}/versions")]
        public async Task<IActionResult> GetSolutionVersions(string sessionId, string problemId)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!session.Collaborators.Contains(userId))
                return Forbid();

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            if (problem.SolutionDocumentId == null)
                return Ok(new List<SolutionVersion>());

            var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);

            return Ok(solutionDoc.Versions);
        }


    [HttpGet("{problemId}/versions/{versionId}")]
        public async Task<IActionResult> GetSolutionVersion(
    string sessionId,
    string problemId,
    string versionId)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!session.Collaborators.Contains(userId))
                return Forbid();

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            if (problem.SolutionDocumentId == null)
                return NotFound("No solution exists");

            var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);
            var version = solutionDoc.Versions.FirstOrDefault(v => v.Id == versionId);

            return version == null ? NotFound() : Ok(version);
        }

        [HttpGet("{problemId}/full")]
        public async Task<IActionResult> GetProblemWithSolution(string sessionId, string problemId)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!session.Collaborators.Contains(userId))
                return Forbid();

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            SolutionVersion? latest = null;

            if (problem.SolutionDocumentId != null)
            {
                var solutionDoc = await _solutions.GetByIdAsync(problem.SolutionDocumentId);
                latest = solutionDoc.Versions.LastOrDefault();
            }

            return Ok(new
            {
                problem,
                latestSolution = latest
            });
        }
        [HttpPost("{problemId}/mark-reused")]
        public async Task<IActionResult> MarkSolutionReused(string sessionId, string problemId)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (!session.Collaborators.Contains(userId))
                return Forbid();

            var problem = await _problems.GetByIdAsync(problemId);
            if (problem == null || problem.SessionId != sessionId)
                return BadRequest("Problem does not belong to this session");

            await _globalKnowledge.IncrementReusedAsync(problem.Id);

            return Ok(new { message = "Marked as reused" });
        }




    }
}








    