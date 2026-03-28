"use client";

import { TOOL_REGISTRY } from "../tools/registry";
import { useSessionUI } from "../state/useSession";

export default function ToolDrawer() {
  const { visibleTools, toggleTool } = useSessionUI();

  return (
    <div className="fixed right-4 top-20 w-72 bg-[#111] border border-white/10 rounded-xl p-4 shadow-xl">
      <h2 className="text-lg font-semibold mb-3">Tools</h2>

      <div className="space-y-3">
        {Object.entries(TOOL_REGISTRY).map(([id, tool]) => {
          const isVisible = visibleTools.includes(id as any);

          return (
            <div
              key={id}
              className="flex items-center justify-between bg-white/5 p-2 rounded-md"
            >
              <div>
                <p className="font-medium">{tool.label}</p>
                <p className="text-xs text-white/50">{tool.description}</p>
              </div>

              <button
                onClick={() => toggleTool(id as any)}
                className={`px-3 py-1 rounded-md border ${
                  isVisible
                    ? "bg-cyan-500/20 border-cyan-500 text-cyan-300"
                    : "bg-white/5 border-white/20 text-white/60"
                }`}
              >
                {isVisible ? "On" : "Off"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
