namespace RealistAPI.Models
{
    public class GlobalKnowledge
    {
        public string Id { get; set; }           // Mongo _id

        public string ProblemId { get; set; }
        public string SessionId { get; set; }

        // stable fingerprint for cross-session reuse
        public string ProblemKey { get; set; }

        public string Domain { get; set; }
        public List<string> Tags { get; set; }

        public string ProblemSummary { get; set; }
        public string SolutionSummary { get; set; }

        // store deep core (for reuse knowledge)
        public string DeepCore { get; set; }

        // lineage (which knowledge items were used to build)
        public List<string> SourceKnowledgeIds { get; set; } = new();

        // routing metadata (to defend cost/intelligence tradeoffs)
        public bool UsedRag { get; set; }
        public bool UsedDeep { get; set; }
        public bool DeepCacheHit { get; set; }
        public bool RagCacheHit { get; set; }

        public double? Confidence { get; set; }
        public DateTime CreatedAt { get; set; }
        public List<double> Embedding { get; set; }

        public int ApprovedCount { get; set; }
        public int OptimizedCount { get; set; }
        public int ReusedCount { get; set; }

        // explicit retrieval ranking score (computed on write or query)
        public double Score { get; set; }
    }
}
