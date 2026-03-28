"use client";

import { useEffect } from "react";
import { useSessionUI } from "../state/useSession";

export default function ActivityFeed({ sessionId }: { sessionId: string }) {
  const { activity, fetchActivity, activeProblem } = useSessionUI();

  useEffect(() => {
    fetchActivity(sessionId);
  }, [activeProblem]);

  if (!activity || activity.length === 0) {
    return (
      <div className="text-white/40 italic">
        No activity yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {activity.map((event) => (
        <div
          key={event.id}
          className="bg-black/20 border border-white/10 rounded-md p-3"
        >
          <div className="text-xs text-white/40">
            {new Date(event.timestamp).toLocaleString()}
          </div>
          <div className="text-white/80 text-sm mt-1">
            {event.message}
          </div>
        </div>
      ))}
    </div>
  );
}
