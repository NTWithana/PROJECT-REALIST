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
    }
}
