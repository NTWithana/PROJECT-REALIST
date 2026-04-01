namespace RealistAPI.Models
{
    public class AiChatResponseDto
    {
            public string Response { get; set; }
            public string Intent { get; set; }
            public double Confidence { get; set; }
            public bool UsedGlobalRag { get; set; }
            public bool UsedDeep { get; set; }
            public List<string> RetrievedGlobalKnowledgeIds { get; set; }
        
    }
}
