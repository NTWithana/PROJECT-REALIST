using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace RealistAPI.Models
{
    public class ProblemDocument
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string Id { get; set; }

        public string SessionId { get; set; }
        public string CreatedByUserId { get; set; }

        public string Description { get; set; }
        public string Suggestions { get; set; }

        public string Domain { get; set; }
        public List<string> Tags { get; set; } = new();

        public string? SolutionDocumentId { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}
