using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using RealistAPI.Interfaces;

namespace RealistAPI.Services
{
    public class SimpleEmbeddingService : IEmbeddingService
    {
        // Shared vocabulary for engineering-ish text (extend as needed)
        private static readonly string[] Vocabulary =
        {
            "api","service","database","cache","queue","event","http","grpc","latency",
            "throughput","scalability","availability","consistency","replication","sharding",
            "index","query","schema","microservice","monolith","docker","kubernetes",
            "load","balancer","retry","circuit","breaker","timeout","security","auth",
            "jwt","encryption","logging","monitoring","metrics","alert","cloud","aws",
            "azure","gcp","network","bandwidth","cpu","memory","disk","io"
        };

        public List<double> GenerateEmbedding(string text)
        {
            var vec = new double[Vocabulary.Length];

            if (string.IsNullOrWhiteSpace(text))
                return vec.ToList();

            var tokens = Tokenize(text);

            var counts = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
            foreach (var t in tokens)
            {
                if (!counts.ContainsKey(t)) counts[t] = 0;
                counts[t]++;
            }

            for (int i = 0; i < Vocabulary.Length; i++)
            {
                counts.TryGetValue(Vocabulary[i], out var c);
                vec[i] = c;
            }

            // L2 normalize
            var norm = Math.Sqrt(vec.Sum(v => v * v));
            if (norm > 0)
            {
                for (int i = 0; i < vec.Length; i++)
                    vec[i] /= norm;
            }

            return vec.ToList();
        }

        private static IEnumerable<string> Tokenize(string text)
        {
            var sb = new StringBuilder();
            foreach (var ch in text.ToLowerInvariant())
            {
                if (char.IsLetterOrDigit(ch))
                    sb.Append(ch);
                else if (sb.Length > 0)
                {
                    yield return sb.ToString();
                    sb.Clear();
                }
            }
            if (sb.Length > 0)
                yield return sb.ToString();
        }
    }
}
