"use client";

import { useEffect } from "react";
import { useSessionUI } from "../state/useSession";

export default function AISuggestions({ sessionId }: { sessionId: string }) {
  const {
    activeProblem,
    aiSuggestions,
    fetchAiSuggestions,
  } = useSessionUI();

  useEffect(() => {
    if (activeProblem) {
      fetchAiSuggestions(sessionId, activeProblem);
    }
  }, [activeProblem]);

  if (!activeProblem) {
    return (
      <div className="text-white/40 italic">
        Select a problem to view AI suggestions.
      </div>
    );
  }

  if (!aiSuggestions) {
    return (
      <div className="text-white/40 italic">
        Loading AI suggestions…
      </div>
    );
  }

  const { critique, improvements, confidence } = aiSuggestions;

  return (
    <div className="space-y-4">

      <div>
        <h3 className="text-sm font-semibold text-white/70 mb-1">Confidence</h3>
        <div className="text-white/90">{confidence?.toFixed(2)}</div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-white/70 mb-1">Critique</h3>
        <div className="text-white/60 whitespace-pre-wrap bg-black/20 p-3 rounded-md border border-white/10">
          {critique || "No critique available."}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-white/70 mb-1">Improvements</h3>
        <div className="text-white/60 whitespace-pre-wrap bg-black/20 p-3 rounded-md border border-white/10">
          {improvements || "No improvements suggested."}
        </div>
      </div>

      <button
        onClick={() => fetchAiSuggestions(sessionId, activeProblem)}
        className="px-3 py-2 bg-white/5 border border-white/10 rounded-md hover:bg-white/10 transition text-white/80"
      >
        Refresh AI Suggestions
      </button>
    </div>
  );
}
