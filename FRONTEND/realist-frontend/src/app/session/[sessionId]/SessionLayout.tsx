"use client";

import { useEffect } from "react";
import { useSessionUI } from "../state/useSession";

import ProblemList from "../components/ProblemList";
import SolutionPanel from "../components/SolutionPanel";
import AISuggestions from "../components/AISuggestions";
import ActivityFeed from "../components/ActivityFeed";
import ChatPanel from "../components/ChatPanel";
import SimilarProblems from "../components/SimilarProblems";
import AiInsights from "../components/AiInsights";
import VersionTimeline from "../components/VersionTimeline";

function DockPanel({
  title,
  children,
  noPadding = false,
}: {
  title?: string;
  children: React.ReactNode;
  noPadding?: boolean;
}) {
  return (
    <div className="bg-white/5 rounded-lg border border-white/10">
      {title && (
        <h2 className="text-lg font-medium px-4 pt-4 mb-2">{title}</h2>
      )}
      <div className={noPadding ? "" : "p-4"}>{children}</div>
    </div>
  );
}

function Placeholder() {
  return <div className="h-40 bg-black/20 rounded-md"></div>;
}

export default function SessionLayout({ sessionId }: { sessionId: string }) {
  const { visibleTools, isSolo, applyPreset } = useSessionUI();

  useEffect(() => {
    applyPreset("deepWork");
  }, []);

  return (
    <div className="flex flex-1 overflow-hidden">

      {/* LEFT DOCK */}
      <aside className="w-[22%] border-r border-white/10 p-4 overflow-y-auto bg-black/20 backdrop-blur-sm">
        <div className="space-y-4">

          {visibleTools.includes("problemList") && (
            <DockPanel title="Problems">
              <ProblemList sessionId={sessionId} />
            </DockPanel>
          )}

          {visibleTools.includes("similarProblems") && (
            <DockPanel title="Similar Problems">
              <SimilarProblems sessionId={sessionId} />
            </DockPanel>
          )}

          {visibleTools.includes("notes") && (
            <DockPanel title="Notes">
              <Placeholder />
            </DockPanel>
          )}

        </div>
      </aside>

      {/* CENTER STAGE */}
      <main className="flex-1 p-4 overflow-y-auto bg-black/10 backdrop-blur-sm">
        <div className="space-y-4">

          {visibleTools.includes("solutionPanel") && (
            <DockPanel title="Solution Panel">
              <SolutionPanel sessionId={sessionId} />
            </DockPanel>
          )}

         {visibleTools.includes("versionTimeline") && (
  <DockPanel title="Version Timeline">
    <VersionTimeline sessionId={sessionId} />
  </DockPanel>
)}

  {visibleTools.includes("aiSuggestions") && (
      <DockPanel title="AI Insights">
    <AiInsights sessionId={sessionId} />
    </DockPanel>
)}


        </div>
      </main>

      {/* RIGHT DOCK */}
      <aside className="w-[28%] border-l border-white/10 p-4 overflow-y-auto bg-black/20 backdrop-blur-sm">
        <div className="space-y-4">

          {(visibleTools.includes("teamChat") ||
            visibleTools.includes("teamAiChat") ||
            visibleTools.includes("privateAi")) && (
            <DockPanel noPadding>
              <ChatPanel sessionId={sessionId} />
            </DockPanel>
          )}

          {!isSolo && visibleTools.includes("activityFeed") && (
            <DockPanel title="Activity Feed">
              <ActivityFeed sessionId={sessionId} />
            </DockPanel>
          )}

        </div>
      </aside>

    </div>
  );
}
