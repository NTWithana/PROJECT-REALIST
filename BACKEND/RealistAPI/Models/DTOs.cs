using System.Text.Json.Serialization;

namespace RealistAPI.Models
{
    public class ProblemReqDto
    {
        public string SessionId { get; set; }
        public string Description { get; set; }
        public string Suggestions { get; set; }
        public string Domain { get; set; }
        public List<string> Tags { get; set; }
    }
}
public class CreateProblemRequest
{
    public string Description { get; set; }
    public string Suggestions { get; set; }
    public string Domain { get; set; }
    public List<string> Tags { get; set; } = new();
}

public class AiEngineResponseDto
{
    public string? Status { get; set; }

    [JsonPropertyName("optimisedSolution")]
    public string? OptimisedSolution { get; set; }

    public double? Confidence { get; set; }
    public string? Rationale { get; set; }
    public int? Iteration { get; set; }

    [JsonPropertyName("created_at")]
    public DateTime? Created_At { get; set; }

    public string? DeepCore { get; set; }
    public string? Critique { get; set; }
    public string? Improvements { get; set; }

    public bool? UsedRag { get; set; }
    public bool? UsedDeep { get; set; }
    public bool? DeepCacheHit { get; set; }
    public bool? RagCacheHit { get; set; }

    public string? ProblemKey { get; set; }

    [JsonPropertyName("retrievedKnowledgeIds")]
    public List<string> RetrievedKnowledgeIds { get; set; } = new();
}


public class FeedbackDto
{
    public List<string> Messages { get; set; }
}

public class EditSolutionRequest
{
    public string NewText { get; set; }
    public string Comment { get; set; }
}

public class ChatAiRequest
{
    public string Message { get; set; }
}

public class ApproveAiRequest
{
   public string MergedText { get; set; }
   public string SuggestionSummary { get; set; }
}


 public class InviteCollaboratorRequest
{
    public string UserId { get; set; }
}

public class CreateSessionRequest
  {
      public string Title { get; set; }
        public string Description { get; set; }
 }
    public class ChatResponseDto
    {
        public string Response { get; set; }
    }



