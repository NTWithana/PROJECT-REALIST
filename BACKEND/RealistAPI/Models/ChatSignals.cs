namespace RealistAPI.Models
{
    public class ChatSignal
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();

        public string DedupKey { get; set; } = default!;

        public string Mode { get; set; } = default!; // chat | hub | supervision
        public string Intent { get; set; } = default!;

        public string Domain { get; set; } = "general";
        public List<string> Tags { get; set; } = new();

        public string Category { get; set; } = default!; // preference | workflow | pain_point | decision_rule
        public string Pattern { get; set; } = default!;
        public double Importance { get; set; }

        public string? SessionId { get; set; }
        public string? UserId { get; set; }

        public double Confidence { get; set; }
        public string ModelUsed { get; set; } = default!;

        public List<string> RetrievedGlobalKnowledgeIds { get; set; } = new();
        public List<string> RetrievedChatSignalIds { get; set; } = new();

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}
