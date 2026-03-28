"use client";

import { useEffect } from "react";
import { useSessionUI } from "../state/useSession";

export default function SolutionPanel({ sessionId }: { sessionId: string }) {
  const { activeProblem, solutionText, setSolutionText } = useSessionUI();

  useEffect(() => {
    if (!activeProblem) return;

    async function loadSolution() {
      const token = localStorage.getItem("token");

      const res = await fetch(
        `/api/sessions/${sessionId}/problems/${activeProblem}/solution`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const data = await res.json();

      if (data.solutionText) {
        setSolutionText(data.solutionText);
      } else {
        setSolutionText("");
      }
    }

    loadSolution();
  }, [activeProblem, sessionId]);

  if (!activeProblem) {
    return (
      <div className="text-white/40 text-sm italic">
        Select a problem to start writing a solution.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <textarea
        value={solutionText}
        onChange={(e) => setSolutionText(e.target.value)}
        placeholder="Write your solution here..."
        className="w-full h-56 bg-black/20 border border-white/10 rounded-md p-3 text-white resize-none focus:outline-none focus:border-cyan-500/50"
      />
      
      <div className="text-right text-white/40 text-xs">
        Auto‑saving…
      </div>
      
    </div>
  );
}
