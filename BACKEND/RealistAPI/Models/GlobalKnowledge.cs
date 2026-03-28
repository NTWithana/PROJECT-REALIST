namespace RealistAPI.Models
{
    public class GlobalKnowledge
    {
        public string Id { get; set; }           // Mongo _id
        public string ProblemId { get; set; }
        public string SessionId { get; set; }
        public string Domain { get; set; }
        public List<string> Tags { get; set; }

        public string ProblemSummary { get; set; }
        public string SolutionSummary { get; set; }

        public double? Confidence { get; set; }
        public DateTime CreatedAt { get; set; }
        public List<double> Embedding { get; set; }
        public int ApprovedCount { get; set; }     
        public int OptimizedCount { get; set; }    
        public int ReusedCount { get; set; }        

    }
}
