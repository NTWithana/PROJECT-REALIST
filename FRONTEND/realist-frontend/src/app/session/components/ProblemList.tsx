"use client";

import { useEffect, useState } from "react";
import { useSessionUI } from "../state/useSession";

export default function ProblemList({ sessionId }: { sessionId: string }) {
  const { activeProblem, setActiveProblem, fetchVersions } = useSessionUI();
  const [problems, setProblems] = useState<any[]>([]);

  useEffect(() => {
    async function loadProblems() {
      const token = localStorage.getItem("token");

      const res = await fetch(`/api/sessions/${sessionId}/problems`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = await res.json();
      setProblems(data);
    }

    loadProblems();
  }, [sessionId]);

  return (
    <div className="space-y-2">
      {problems.map((p) => (
        <button
          key={p.id}
          onClick={() => {
            setActiveProblem(p.id);
            fetchVersions(sessionId, p.id);
          }}
          className={`w-full text-left px-3 py-2 rounded-md border ${
            activeProblem === p.id
              ? "bg-cyan-500/20 border-cyan-500 text-cyan-300"
              : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
          }`}
        >
          {p.description}
        </button>
      ))}
    </div>
  );
}
