"use client";

import { ReactNode, useEffect } from "react";
import { useSessionUI } from "../state/useSession";


type WorkspaceShellProps = {
  sessionId: string;
  children: ReactNode;
};

export default function WorkspaceShell({ sessionId, children }: WorkspaceShellProps) {
  const { collaborators, isSolo, applyPreset } = useSessionUI();

  useEffect(() => {
    applyPreset("deepWork");
  }, []);

  return (
    <div className="h-screen w-full bg-[#050509] text-white flex flex-col">
      {/* TOP BAR */}
      <header className="h-14 border-b border-white/10 flex items-center justify-between px-5 bg-black/60 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="h-7 w-7 rounded-md bg-cyan-500/20 border border-cyan-500/40" />
          <div className="flex flex-col">
            <span className="text-xs text-white/40 uppercase tracking-[0.18em]">
              REALIST WORKSPACE
            </span>
            <span className="text-sm text-white/80">
              Session #{sessionId.slice(0, 6)} •{" "}
              {isSolo ? "Solo" : `${collaborators.length} collaborators`}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-white/50">
          <span className="px-2 py-1 rounded-md bg-white/5 border border-white/10">
            Global AI Linked
          </span>
          <span className="px-2 py-1 rounded-md bg-white/5 border border-white/10">
            Session Memory Live
          </span>
        </div>
      </header>

      {/* MAIN GRID */}
      <div className="flex flex-1 overflow-hidden relative">
        {children}

        {/* BACKGROUND ACCENTS */}
        <div className="absolute -bottom-20 -right-20 w-60 h-60 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-16 -left-16 w-72 h-72 bg-pink-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>
    </div>
  );
}
