"use client";

import { useSupervisor } from "@/lib/os/useSupervisor";

export default function SupervisorPanel({
  sessionId,
}: {
  sessionId: string;
}) 
 {
  const { summary, risks, nextActions, loading } = useSupervisor();

  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-4">
      <h3 className="text-white/70 text-sm mb-2">Session Supervisor</h3>

      {loading && (
        <div className="text-white/40 text-xs animate-pulse">Analyzing…</div>
      )}

      {summary && (
        <p className="text-white/80 text-sm mb-3">{summary}</p>
      )}

      {risks && risks.length > 0 && (
        <div className="text-red-300 text-xs mb-3">
          <strong>Risks:</strong>
          <ul className="list-disc ml-4">
            {risks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {nextActions && nextActions.length > 0 && (
        <div className="text-cyan-300 text-xs">
          <strong>Next Actions:</strong>
          <ul className="list-disc ml-4">
            {nextActions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
