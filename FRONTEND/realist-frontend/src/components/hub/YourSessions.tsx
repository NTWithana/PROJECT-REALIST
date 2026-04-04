"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function YourSessions() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  //  STUB FUNCTION  remove when using) ---
  async function fetchUserSessions() {
    return [
      {
        id: "demo-session-1",
        title: "Catalyst OS Architecture",
        updatedAt: new Date().toISOString(),
      },
    ];
  }

  useEffect(() => {
    async function load() {
      const data = await fetchUserSessions();
      setSessions(data);
      setLoading(false);
    }
    load();
  }, []);

  // --- UI STATES ---

  if (loading) {
    return <div className="text-white/40 text-sm">Loading sessions…</div>;
  }

  if (sessions.length === 0) {
    return (
      <div className="text-white/40 text-sm">
        You have no sessions yet.
        <br />
        Start one using “New Session”.
      </div>
    );
  }

  // --- MAIN RENDER ---
  return (
    <div className="space-y-3">
      {sessions.map((s) => (
        <Link
          key={s.id}
          href={`/session/${s.id}`}
          className="block bg-white/5 border border-white/10 rounded-md p-3 hover:bg-white/10 transition"
        >
          <div className="text-white/90 font-medium">{s.title}</div>

          <div className="text-white/40 text-xs mt-1">
            {s.description || "No description"}
          </div>

          <div className="text-white/30 text-xs mt-1">
            Last updated: {new Date(s.updatedAt).toLocaleString()}
          </div>
        </Link>
      ))}
    </div>
  );
}
