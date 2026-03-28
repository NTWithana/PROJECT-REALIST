namespace RealistAPI.Models
{
    public class ConsistencyIssue
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string ProblemAId { get; set; } = default!;
        public string ProblemBId { get; set; } = default!;
        public string Description { get; set; } = default!;
        public double Confidence { get; set; }
        public bool CanAutoAlign { get; set; } = true;
    }
}
