"use client";

import { useEffect } from "react";
import { useCatalystOS } from "@/lib/os/useCatalystOS";
import WorkspaceShell from "./WorkspaceShell";
import SessionLayout from "./SessionLayout";


export default function Page({ params }: { params: { sessionId: string } }) {
  const { sessionId } = params;
  const { setMode } = useCatalystOS();

  useEffect(() => {
    setMode("focus");
    return () => setMode("global");
  }, []);

  return (
    <>
      {/* OS-level Focus Mode Banner */}
      <div className="w-full bg-black/50 border-b border-white/10 backdrop-blur px-6 py-3 text-sm">
        <span className="text-cyan-300 font-semibold">Focus Mode</span>
        <span className="text-white/50 ml-2">
          — Deep reasoning active. Global intelligence remains available.
        </span>
      </div>

      {/* Workspace */}
      <WorkspaceShell sessionId={sessionId}>
        <SessionLayout sessionId={sessionId} />
      </WorkspaceShell>
    </>
  );
}