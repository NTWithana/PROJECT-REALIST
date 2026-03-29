"use client";

import { useState } from "react";
import { useSessionUI } from "../state/useSession";

export default function ChatPanel({ sessionId }: { sessionId: string }) {
  const {
    isSolo,
    activeProblem,
    teamMessages,
    privateAiMessages,
    sendTeamMessage,
    sendPrivateAiMessage,
  } = useSessionUI();

  const [activeTab, setActiveTab] = useState(isSolo ? "private" : "team");
  const [input, setInput] = useState("");

  const messages =
    activeTab === "team" ? teamMessages : privateAiMessages;

  const send = () => {
    if (!input.trim()) return;

    if (activeTab === "team") {
      sendTeamMessage(sessionId, input);
    } else {
      sendPrivateAiMessage(sessionId, activeProblem, input);
    }

    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-white/10">
        {!isSolo && (
          <Tab active={activeTab === "team"} onClick={() => setActiveTab("team")}>
            Team Chat
          </Tab>
        )}

        {!isSolo && (
          <Tab active={activeTab === "teamAi"} onClick={() => setActiveTab("teamAi")}>
            AI for Team
          </Tab>
        )}

        <Tab active={activeTab === "private"} onClick={() => setActiveTab("private")}>
          My AI
        </Tab>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 p-3 bg-black/20">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`p-2 rounded-md border border-white/10 ${
              m.sender === "user" ? "bg-white/10" : "bg-black/30"
            }`}
          >
            <div className="text-xs text-white/40">
              {new Date(m.timestamp).toLocaleTimeString()}
            </div>
            <div className="text-white/80 text-sm mt-1">{m.text}</div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-white/10 flex gap-2">
        <input
          className="flex-1 bg-black/30 border border-white/10 rounded-md px-3 py-2 text-white"
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          onClick={send}
          className="px-4 py-2 bg-white/10 border border-white/20 rounded-md hover:bg-white/20"
        >
          Send
        </button>
      </div>
    </div>
  );
}

// props
function Tab({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 py-2 text-center ${
        active ? "bg-white/10 text-white" : "text-white/50 hover:bg-white/5"
      }`}
    >
      {children}
    </button>
  );
}