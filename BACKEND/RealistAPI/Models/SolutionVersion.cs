namespace RealistAPI.Models
{
    public class SolutionVersion
    {
        public string Id { get; set; }
        public string SolutionText { get; set; }
        public string Critique { get; set; }
        public string Improvements { get; set; }
        public int Iteration { get; set; }
        public double Confidence { get; set; }
        public DateTime Created_At { get; set; }

        //TO store hybrid artifacts
        public string DeepCore { get; set; }
        public bool UsedRag { get; set; }
        public bool UsedDeep { get; set; }
        public bool DeepCacheHit { get; set; }
        public bool RagCacheHit { get; set; }
        public string ProblemKey { get; set; }
        public List<string> RetrievedKnowledgeIds { get; set; } = new();
    }
}
