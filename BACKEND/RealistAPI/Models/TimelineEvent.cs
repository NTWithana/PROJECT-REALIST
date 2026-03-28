namespace RealistAPI.Models
{
    public class TimelineEvent
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Type { get; set; } = default!; // "problem_created", "solution_version"
        public string? ProblemId { get; set; }
        public string? VersionId { get; set; }
        public string? UserId { get; set; }
        public string? Message { get; set; }
        public DateTime Timestamp { get; set; }
    }
}
