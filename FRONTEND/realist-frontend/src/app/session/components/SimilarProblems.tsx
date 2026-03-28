"use client";

import { useEffect } from "react";
import { useSessionUI } from "../state/useSession";

export default function SimilarProblems({ sessionId }: { sessionId: string }) {
  const {
    activeProblem,
    similarProblems,
    fetchSimilarProblems,
    setActiveProblem,
  } = useSessionUI();

  useEffect(() => {
    if (activeProblem) {
      fetchSimilarProblems(sessionId, activeProblem);
    }
  }, [activeProblem]);

  if (!activeProblem) {
    return (
      <div className="text-white/40 italic">
        Select a problem to view similar ones.
      </div>
    );
  }

  if (!similarProblems || similarProblems.length === 0) {
    return (
      <div className="text-white/40 italic">
        No similar problems found.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {similarProblems.map((p) => (
        <button
          key={p.id}
          onClick={() => setActiveProblem(p.id)}
          className="w-full text-left bg-black/20 border border-white/10 rounded-md p-3 hover:bg-white/10 transition"
        >
          <div className="text-white/90 font-medium">{p.title}</div>
          <div className="text-white/50 text-sm mt-1">{p.snippet}</div>
        </button>
      ))}
    </div>
  );
}
