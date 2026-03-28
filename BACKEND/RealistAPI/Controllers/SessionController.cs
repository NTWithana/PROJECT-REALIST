using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using RealistAPI.Interfaces;
using RealistAPI.Models;
using static FeedbackDto;

namespace RealistAPI.Controllers
{
    [ApiController]
    [Route("api/sessions")]
    public class SessionController : ControllerBase
    {
        private readonly ISessionRepository _sessions;
        private readonly IProblemRepository _problems;
        private readonly ISolutionRepository _solutions;

        public SessionController(
            ISessionRepository sessions,
            IProblemRepository problems,
            ISolutionRepository solutions)
        {
            _sessions = sessions;
            _problems = problems;
            _solutions = solutions;
        }

        // CREATE SESSION

        [HttpPost]
        [Authorize]
        public async Task<IActionResult> CreateSession([FromBody] CreateSessionRequest req)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = new CollaborationSession
            {
                LeaderId = userId,
                Collaborators = new List<string> { userId },
                Title = req.Title,
                Description = req.Description
            };

            await _sessions.CreateAsync(session);
            return Ok(session);
        }



        // ADD MESSAGE

        [HttpPost("{id}/messages")]
        [Authorize]
        public async Task<IActionResult> AddMessage(string id, [FromBody] string content)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(id);
            if (session == null) return NotFound();

            if (!session.Collaborators.Contains(userId))
                return Forbid("Only collaborators can post messages");

            var msg = new ChatMessage
            {
                Sender = userId,
                Content = content,
                Timestamp = DateTime.UtcNow
            };

            session.Messages.Add(msg);
            await _sessions.UpdateAsync(session);

            return Ok(session);
        }

        // GET SESSION
        
        [HttpGet("{id}")]
        public async Task<IActionResult> GetSession(string id)
        {
            var session = await _sessions.GetByIdAsync(id);
            return session == null ? NotFound() : Ok(session);
        }

        
        // INVITE COLLABORATOR
      
        [HttpPost("{sessionId}/invite")]
        [Authorize]
        public async Task<IActionResult> InviteCollaborator(
            string sessionId,
            [FromBody] InviteCollaboratorRequest req)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(sessionId);
            if (session == null) return NotFound("Session not found");

            if (session.LeaderId != userId)
                return Forbid("Only the session leader can invite collaborators");

            if (req.UserId == userId)
                return BadRequest("You cannot invite yourself");

            if (session.Collaborators.Contains(req.UserId))
                return BadRequest("User is already a collaborator");

            session.Collaborators.Add(req.UserId);
            await _sessions.UpdateAsync(session);

            return Ok(new
            {
                Message = "Collaborator added successfully",
                Collaborators = session.Collaborators
            });
        }

       
        // GET MY SESSIONS
        
        [HttpGet("my")]
        [Authorize]
        public async Task<IActionResult> GetMySessions()
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var allSessions = await _sessions.GetAllAsync();

            var mySessions = allSessions
                .Where(s => s.LeaderId == userId || s.Collaborators.Contains(userId))
                .ToList();

            return Ok(mySessions);
        }

        
        // SESSION TIMELINE
       
        [HttpGet("{id}/timeline")]
        [Authorize]
        public async Task<IActionResult> GetTimeline(string id)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(id);
            if (session == null) return NotFound("Session not found");

            if (!session.Collaborators.Contains(userId))
                return Forbid();

            var problems = await _problems.GetBySessionAsync(id);

            var events = new List<TimelineEvent>();

            // Problem created
            foreach (var p in problems)
            {
                events.Add(new TimelineEvent
                {
                    Type = "problem_created",
                    ProblemId = p.Id,
                    UserId = p.CreatedByUserId,
                    Timestamp = p.CreatedAt
                });
            }

            // Active problem changes
            foreach (var change in session.ActiveProblemChanges)
            {
                events.Add(new TimelineEvent
                {
                    Type = "active_problem_changed",
                    ProblemId = change.ProblemId,
                    UserId = change.ChangedByUserId,
                    Timestamp = change.Timestamp
                });
            }

            // Solution versions
            foreach (var p in problems)
            {
                if (p.SolutionDocumentId == null) continue;

                var doc = await _solutions.GetByIdAsync(p.SolutionDocumentId);
                foreach (var v in doc.Versions)
                {
                    events.Add(new TimelineEvent
                    {
                        Type = "solution_version",
                        ProblemId = p.Id,
                        VersionId = v.Id,
                        Timestamp = v.Created_At
                    });
                }
            }

            var ordered = events.OrderBy(e => e.Timestamp).ToList();
            return Ok(ordered);
        }
        [HttpGet("{id}/consistency")]
        [Authorize]
        public async Task<IActionResult> GetConsistency(string id)
        {
            var userId = User.FindFirst("sub")?.Value;
            if (userId == null) return Unauthorized();

            var session = await _sessions.GetByIdAsync(id);
            if (session == null) return NotFound("Session not found");

            if (!session.Collaborators.Contains(userId))
                return Forbid();

            var problems = await _problems.GetBySessionAsync(id);
            var issues = new List<ConsistencyIssue>();

            var list = problems.ToList();
            for (int i = 0; i < list.Count; i++)
            {
                for (int j = i + 1; j < list.Count; j++)
                {
                    var a = list[i];
                    var b = list[j];

                    // simple relation: same domain or overlapping tags
                    bool sameDomain = !string.IsNullOrEmpty(a.Domain) &&
                                      a.Domain == b.Domain;

                    bool sharedTag = (a.Tags ?? new List<string>())
                        .Intersect(b.Tags ?? new List<string>())
                        .Any();

                    if (!sameDomain && !sharedTag) continue;

                    issues.Add(new ConsistencyIssue
                    {
                        ProblemAId = a.Id,
                        ProblemBId = b.Id,
                        Description = "Related problems detected by domain/tags. Review for consistency.",
                        Confidence = sameDomain && sharedTag ? 0.9 : 0.7,
                        CanAutoAlign = false // v1: just insight, no auto-fix yet
                    });
                }
            }

            return Ok(issues);
        }









    }
}
