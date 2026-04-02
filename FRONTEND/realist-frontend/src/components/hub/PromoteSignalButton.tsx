"use client";

import { ChatSignal } from "@/lib/os/types/ChatSignal";
import { apiFetch } from "@/lib/api/client";

export default function PromoteSignalButton({ signal }: { signal: ChatSignal }) {
  async function promote() {
    await apiFetch("/api/knowledge/promote", {
      method: "POST",
      body: JSON.stringify(signal),
    });
  }

  return (
    <button
      onClick={promote}
      className="text-xs text-cyan-300 hover:underline"
    >
      Promote to Global Knowledge
    </button>
  );
}
