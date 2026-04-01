"use client";

import { apiFetch } from "@/lib/api/client";
import { useState } from "react";

type SemanticResult = {
  problem_summary: string;
  solution_summary: string;
  domain: string;
  tags: string[];
  confidence: number;
  approved_count: number;
  optimized_count: number;
  reused_count: number;
};

export default function GlobalSearchPanel() {
  const [query, setQuery] = useState("");
  const [aiInsight, setAiInsight] = useState<string | null>(null);
  const [semanticResults, setSemanticResults] = useState<SemanticResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [meta, setMeta] = useState<{
    intent: string;
    confidence: number;
    usedRag: boolean;
    usedDeep: boolean;
    retrievedKnowledgeIds: string[];
  } | null>(null);

  async function runUnifiedSearch() {
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setAiInsight(null);
    setSemanticResults([]);

    const semanticReq = fetch(
      `/api/knowledge/semantic-similar?query=${encodeURIComponent(query)}`
    ).then((res) => res.json());

    const aiReq = apiFetch("/api/hub/assistant", {
      method: "POST",
      body: JSON.stringify({ message: query }),
    }).then((res) => res.json());

    const [semanticData, aiData] = await Promise.all([semanticReq, aiReq]);

    setSemanticResults(semanticData || []);
    setAiInsight(aiData.response);
    setMeta(aiData.meta);

    setLoading(false);
  }

  return (
    <div className="space-y-6">

      <div className="bg-white/5 border border-white/10 rounded-lg p-4">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runUnifiedSearch()}
          placeholder="What do you want to know?"
          className="w-full p-3 bg-black/20 border border-white/10 rounded-md text-white placeholder-white/40 focus:outline-none focus:border-cyan-500 transition"
        />

        <button
          onClick={runUnifiedSearch}
          className="mt-3 w-full py-2 bg-cyan-600/20 border border-cyan-600 rounded-md text-cyan-200 hover:bg-cyan-600/30 transition"
        >
          Search
        </button>
      </div>

      {loading && (
        <div className="text-white/40 text-sm animate-pulse">
          Thinking…
        </div>
      )}

      {!loading && searched && !aiInsight && semanticResults.length === 0 && (
        <div className="text-white/40 text-sm">
          No global knowledge found. Try a broader query.
        </div>
      )}

      {meta && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 text-sm space-y-1">
          <div>
            Interpreted as: <span className="text-cyan-300">{meta.intent}</span>
          </div>
          <div>Confidence: {(meta.confidence * 100).toFixed(0)}%</div>
          <div>Global knowledge used: {meta.usedRag ? "Yes" : "No"}</div>
          <div>Deep reasoning: {meta.usedDeep ? "Yes" : "No"}</div>
        </div>
      )}

      {aiInsight && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-2">
          <h3 className="text-white/70 text-sm">AI Insight</h3>
          <p className="text-white/90 text-sm leading-relaxed">
            {aiInsight}
          </p>
        </div>
      )}

      {semanticResults.length > 0 && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-3">
          <h3 className="text-white/70 text-sm">Semantic Matches</h3>

          {semanticResults.map((item, i) => (
            <div
              key={i}
              className="p-3 bg-black/20 border border-white/10 rounded-md space-y-1"
            >
              <div className="text-white/90 text-sm font-medium">
                {item.problem_summary}
              </div>

              <div className="text-white/50 text-xs">
                {item.solution_summary}
              </div>

              <div className="flex flex-wrap gap-2 mt-2 text-xs text-white/40">
                {item.domain && (
                  <span className="px-2 py-0.5 bg-white/5 border border-white/10 rounded-md">
                    {item.domain}
                  </span>
                )}

                {item.tags?.map((t) => (
                  <span
                    key={t}
                    className="px-2 py-0.5 bg-white/5 border border-white/10 rounded-md"
                  >
                    {t}
                  </span>
                ))}
              </div>

              <div className="text-white/30 text-xs mt-2">
                Confidence: {item.confidence.toFixed(2)} • Approved:{" "}
                {item.approved_count} • Optimized: {item.optimized_count} •
                Reused: {item.reused_count}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
