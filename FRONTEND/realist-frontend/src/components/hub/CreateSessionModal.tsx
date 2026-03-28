"use client";

import { useState } from "react";

export default function CreateSessionModal({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [mode, setMode] = useState<"solo" | "team">("solo");

  async function createSession() {
    const token = localStorage.getItem("token");

    const res = await fetch("/api/sessions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        title,
        description,
        mode
      })
    });

    const data = await res.json();
    window.location.href = `/session/${data.id}`;
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center">
      <div className="bg-[#111] border border-white/10 rounded-xl p-6 w-[420px]">

        <h2 className="text-xl font-semibold mb-4">Create New Session</h2>

        <input
          className="w-full mb-3 p-2 bg-black/20 border border-white/10 rounded-md"
          placeholder="Session title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <textarea
          className="w-full mb-3 p-2 bg-black/20 border border-white/10 rounded-md"
          placeholder="Short description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        <div className="flex gap-3 mb-4">
          <button
            onClick={() => setMode("solo")}
            className={`px-3 py-1 rounded-md border ${
              mode === "solo"
                ? "bg-cyan-500/20 border-cyan-500 text-cyan-300"
                : "bg-white/5 border-white/10"
            }`}
          >
            Solo
          </button>

          <button
            onClick={() => setMode("team")}
            className={`px-3 py-1 rounded-md border ${
              mode === "team"
                ? "bg-cyan-500/20 border-cyan-500 text-cyan-300"
                : "bg-white/5 border-white/10"
            }`}
          >
            Team
          </button>
        </div>

        <button
          onClick={createSession}
          className="w-full py-2 bg-cyan-600/20 border border-cyan-600 rounded-md hover:bg-cyan-600/30"
        >
          Create Session
        </button>

        <button
          onClick={onClose}
          className="mt-4 text-white/40 hover:text-white text-sm"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
