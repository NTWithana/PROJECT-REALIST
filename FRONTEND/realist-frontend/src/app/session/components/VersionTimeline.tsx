"use client";

import { useEffect } from "react";
import { useSessionUI } from "../state/useSession";

export default function VersionTimeline({ sessionId }: { sessionId: string }) {
  const { timeline, fetchTimeline } = useSessionUI();

  useEffect(() => {
    fetchTimeline(sessionId);
  }, [sessionId, fetchTimeline]);

  if (!timeline.length) {
    return (
      <div className="text-white/40 text-sm italic">
        No activity yet in this session.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {timeline.map((ev) => (
        <div
          key={ev.id}
          className="bg-black/20 border border-white/10 rounded-md p-3"
        >
          <div className="text-xs text-white/40">
            {new Date(ev.timestamp).toLocaleString()}
          </div>
          <div className="text-sm text-white/80 mt-1">
            {renderLabel(ev)}
          </div>
        </div>
      ))}
    </div>
  );
}

function renderLabel(ev: any) {
  switch (ev.type) {
    case "problem_created":
      return `Problem created (ID: ${ev.problemId})`;
    case "active_problem_changed":
      return `Active problem changed to ${ev.problemId}`;
    case "solution_version":
      return `New solution version created (v: ${ev.versionId})`;
    default:
      return ev.type;
  }
}
