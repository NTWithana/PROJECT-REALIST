public class ChatMessage
{
    public string Sender { get; set; }   // "human" or "ai"
    public string Content { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}

