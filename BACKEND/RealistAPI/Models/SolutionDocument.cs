using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace RealistAPI.Models
{
    public class SolutionDocument
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string Id { get; set; }

        public string ProblemId { get; set; }
        public List<SolutionVersion> Versions { get; set; } = new();
    }
}
