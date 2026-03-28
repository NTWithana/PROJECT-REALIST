"use client";

import { useEffect } from "react";
import { useSessionUI } from "../state/useSession";

export default function AiInsights({ sessionId }: { sessionId: string }) {
  const { consistency, fetchConsistency } = useSessionUI();

  useEffect(() => {
    fetchConsistency(sessionId);
  }, [sessionId, fetchConsistency]);

  if (!consistency.length) {
    return (
      <div className="text-white/40 text-sm italic">
        No cross-problem relationships detected yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {consistency.map((issue) => (
        <div
          key={issue.id}
          className="bg-black/20 border border-white/10 rounded-md p-3"
        >
          <div className="text-xs text-white/40">
            Confidence: {(issue.confidence * 100).toFixed(0)}%
          </div>
          <div className="text-sm text-white/80 mt-1">
            {issue.description}
          </div>
          <div className="text-xs text-white/50 mt-1">
            Problem A: {issue.problemAId} • Problem B: {issue.problemBId}
          </div>
        </div>
      ))}
    </div>
  );
}
