using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

public class CollaborationSession
{
    [BsonId]
    [BsonRepresentation(BsonType.ObjectId)]
    public string Id { get; set; }

    public string LeaderId { get; set; }
    public List<string> Collaborators { get; set; } = new();

    public List<ChatMessage> Messages { get; set; } = new();

    public string? ActiveProblemId { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public List<ActiveProblemChange> ActiveProblemChanges { get; set; } = new();

    public string Title { get; set; }
    public string Description { get; set; }

}
public class ActiveProblemChange
{
    public string ProblemId { get; set; }
    public string ChangedByUserId { get; set; }
    public DateTime Timestamp { get; set; }
}