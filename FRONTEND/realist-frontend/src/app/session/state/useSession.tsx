"use client";

import { create } from "zustand";
import type { ToolId } from "../tools/registry";
import React from "react";

// -----------------------------
// TYPES
// -----------------------------

export type LayoutPreset = "deepWork" | "collab" | "research";

type Version = {
  id: string;
  solutionText: string;
  created_At: string;
};

type AiSuggestions = {
  critique: string | null;
  improvements: string | null;
  confidence: number | null;
} | null;

export type ActivityEvent = {
  id: string;
  type: string;
  message?: string | null;
  timestamp: string;
  problemId?: string | null;
  versionId?: string | null;
  userId?: string | null;
};

export type ChatMessage = {
  id: string;
  sender: "user" | "ai" | "system" | string;
  text: string;
  timestamp: string;
};

export type SimilarProblem = {
  id: string;
  title: string;
  snippet: string;
};

export type WindowInstance = {
  id: string;
  title: string;
  content: React.ReactNode;
  width: number;
  height: number;
  x: number;
  y: number;
};

export type ConsistencyIssue = {
  id: string;
  problemAId: string;
  problemBId: string;
  description: string;
  confidence: number;
  canAutoAlign: boolean;
};

export type TimelineEvent = ActivityEvent;

// -----------------------------
// STATE TYPE
// -----------------------------

type SessionUiState = {
  // TOOL STATE
  visibleTools: ToolId[];
  hiddenTools: ToolId[];
  pinnedTools: ToolId[];
  aiSuggestedTools: ToolId[];

  // CHAT
  teamMessages: ChatMessage[];
  privateAiMessages: ChatMessage[];

  setTeamMessages: (list: ChatMessage[]) => void;
  setPrivateAiMessages: (list: ChatMessage[]) => void;

  sendTeamMessage: (sessionId: string, text: string) => Promise<void>;
  sendPrivateAiMessage: (
    sessionId: string,
    problemId: string | null,
    text: string
  ) => Promise<void>;

  // SIMILAR PROBLEMS
  similarProblems: SimilarProblem[];
  setSimilarProblems: (list: SimilarProblem[]) => void;
  fetchSimilarProblems: (
    sessionId: string,
    problemId: string
  ) => Promise<void>;

  // WINDOW SYSTEM
  windows: WindowInstance[];
  activeWindowId: string | null;

  openWindow: (win: Omit<WindowInstance, "id">) => void;
  closeWindow: (id: string) => void;
  focusWindow: (id: string) => void;

  openSimpleWindow: (title: string, content: React.ReactNode) => void;

  // COLLABORATION
  collaborators: string[];
  isSolo: boolean;

  // PROBLEM + SOLUTION
  activeProblem: string | null;
  solutionText: string;
  versions: Version[];

  // AI SUGGESTIONS
  aiSuggestions: AiSuggestions;

  // ACTIVITY FEED
  activity: ActivityEvent[];
  setActivity: (list: ActivityEvent[]) => void;
  fetchActivity: (sessionId: string) => Promise<void>;

  // TIMELINE + CONSISTENCY
  timeline: TimelineEvent[];
  consistency: ConsistencyIssue[];

  setTimeline: (list: TimelineEvent[]) => void;
  setConsistency: (list: ConsistencyIssue[]) => void;

  fetchTimeline: (sessionId: string) => Promise<void>;
  fetchConsistency: (sessionId: string) => Promise<void>;

  // PRESETS
  preset: LayoutPreset;
  setPreset: (p: LayoutPreset) => void;
  applyPreset: (p: LayoutPreset) => void;

  // MUTATORS
  setActiveProblem: (id: string) => void;
  setSolutionText: (text: string) => void;
  setCollaborators: (list: string[]) => void;

  setVersions: (list: Version[]) => void;
  fetchVersions: (sessionId: string, problemId: string) => Promise<void>;
  revertToVersion: (
    sessionId: string,
    problemId: string,
    versionId: string
  ) => Promise<void>;

  setAiSuggestions: (data: AiSuggestions) => void;
  fetchAiSuggestions: (sessionId: string, problemId: string) => Promise<void>;

  toggleTool: (tool: ToolId) => void;
  pinTool: (tool: ToolId) => void;
  unpinTool: (tool: ToolId) => void;
};

// -----------------------------
// STORE
// -----------------------------

export const useSessionUI = create<SessionUiState>((set) => ({
  // TOOL STATE
  visibleTools: ["problemList", "solutionPanel", "versionTimeline", "privateAi"],
  hiddenTools: [],
  pinnedTools: [],
  aiSuggestedTools: [],

  // CHAT
  teamMessages: [],
  privateAiMessages: [],

  setTeamMessages: (list) => set({ teamMessages: list }),
  setPrivateAiMessages: (list) => set({ privateAiMessages: list }),

  sendTeamMessage: async (sessionId, text) => {
    const token = localStorage.getItem("token");

    const res = await fetch(`/api/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) return;

    const updated = await res.json();
    set({ teamMessages: updated });
  },

  sendPrivateAiMessage: async (sessionId, problemId, text) => {
    const token = localStorage.getItem("token");

    const res = await fetch(
      `/api/sessions/${sessionId}/problems/${problemId}/ask-ai`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text }),
      }
    );

    if (!res.ok) return;

    const data = await res.json();

    set((state) => ({
      privateAiMessages: [
        ...state.privateAiMessages,
        {
          id: crypto.randomUUID(),
          sender: "user",
          text,
          timestamp: new Date().toISOString(),
        },
        {
          id: crypto.randomUUID(),
          sender: "ai",
          text: data.answer,
          timestamp: new Date().toISOString(),
        },
      ],
    }));
  },

  // SIMILAR PROBLEMS
  similarProblems: [],

  setSimilarProblems: (list) => set({ similarProblems: list }),

  fetchSimilarProblems: async (sessionId, problemId) => {
    const token = localStorage.getItem("token");

    const res = await fetch(
      `/api/sessions/${sessionId}/problems/${problemId}/similar`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    if (res.status === 404) {
      set({
        similarProblems: [
          {
            id: "demo1",
            title: "No RAG endpoint yet",
            snippet: "This is placeholder data until backend is ready.",
          },
        ],
      });
      return;
    }

    if (!res.ok) return;

    const data = await res.json();
    set({ similarProblems: data });
  },

  // WINDOW SYSTEM
  windows: [],
  activeWindowId: null,

  openWindow: (win) =>
    set((state) => {
      const id = crypto.randomUUID();
      return {
        windows: [...state.windows, { id, ...win }],
        activeWindowId: id,
      };
    }),

  closeWindow: (id) =>
    set((state) => ({
      windows: state.windows.filter((w) => w.id !== id),
      activeWindowId: state.activeWindowId === id ? null : state.activeWindowId,
    })),

  focusWindow: (id) => set({ activeWindowId: id }),

  openSimpleWindow: (title, content) =>
    set((state) => ({
      windows: [
        ...state.windows,
        {
          id: crypto.randomUUID(),
          title,
          content,
          width: 500,
          height: 400,
          x: 200,
          y: 150,
        },
      ],
    })),

  // COLLABORATION
  collaborators: [],
  isSolo: true,

  activeProblem: null,
  solutionText: "",
  versions: [],

  aiSuggestions: null,

  // ACTIVITY FEED
  activity: [],
  setActivity: (list) => set({ activity: list }),

  fetchActivity: async (sessionId) => {
    const token = localStorage.getItem("token");

    const res = await fetch(`/api/sessions/${sessionId}/activity`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) return;

    const data = await res.json();
    set({ activity: data });
  },

  // TIMELINE + CONSISTENCY
  timeline: [],
  consistency: [],

  setTimeline: (list) => set({ timeline: list }),
  setConsistency: (list) => set({ consistency: list }),

  fetchTimeline: async (sessionId) => {
    const token = localStorage.getItem("token");

    const res = await fetch(`/api/sessions/${sessionId}/timeline`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) return;

    const data = await res.json();
    set({ timeline: data });
  },

  fetchConsistency: async (sessionId) => {
    const token = localStorage.getItem("token");

    const res = await fetch(`/api/sessions/${sessionId}/consistency`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) return;

    const data = await res.json();
    set({ consistency: data });
  },

  // PRESETS
  preset: "deepWork",

  setPreset: (p) => set({ preset: p }),

  applyPreset: (p) =>
    set(() => {
      if (p === "deepWork") {
        return {
          preset: p,
          visibleTools: [
            "problemList",
            "solutionPanel",
            "versionTimeline",
            "privateAi",
          ],
        };
      }

      if (p === "collab") {
        return {
          preset: p,
          visibleTools: [
            "problemList",
            "solutionPanel",
            "teamChat",
            "teamAiChat",
            "activityFeed",
          ],
        };
      }

      if (p === "research") {
        return {
          preset: p,
          visibleTools: [
            "problemList",
            "similarProblems",
            "notes",
            "aiSuggestions",
            "privateAi",
          ],
        };
      }

      return {};
    }),

  // MUTATORS
  setActiveProblem: (id) => set({ activeProblem: id }),

  setSolutionText: (text) => set({ solutionText: text }),

  setCollaborators: (list) =>
    set({
      collaborators: list,
      isSolo: list.length <= 1,
    }),

  setVersions: (list) => set({ versions: list }),

  fetchVersions: async (sessionId, problemId) => {
    const token = localStorage.getItem("token");

    const res = await fetch(
      `/api/sessions/${sessionId}/problems/${problemId}/versions`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    if (!res.ok) return;

    const data = await res.json();
    set({ versions: data });
  },

  revertToVersion: async (sessionId, problemId, versionId) => {
    const token = localStorage.getItem("token");

    const res = await fetch(
      `/api/sessions/${sessionId}/problems/${problemId}/versions/${versionId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    if (!res.ok) return;

    const version = await res.json();

    await fetch(`/api/sessions/${sessionId}/problems/${problemId}/edit`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        newText: version.solutionText,
        comment: "Reverted to previous version",
      }),
    });

    set({ solutionText: version.solutionText });

    const versionsRes = await fetch(
      `/api/sessions/${sessionId}/problems/${problemId}/versions`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    if (!versionsRes.ok) return;

    const updated = await versionsRes.json();
    set({ versions: updated });
  },

  // AI SUGGESTIONS
  setAiSuggestions: (data) => set({ aiSuggestions: data }),

  fetchAiSuggestions: async (sessionId, problemId) => {
    const token = localStorage.getItem("token");

    const res = await fetch(
      `/api/sessions/${sessionId}/problems/${problemId}/solution`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    if (!res.ok) return;

    const data = await res.json();

    set({
      aiSuggestions: {
        critique: data.critique ?? null,
        improvements: data.improvements ?? null,
        confidence: data.confidence ?? null,
      },
    });
  },

  // TOOL CONTROLS
  toggleTool: (tool) =>
    set((state) => {
      const isVisible = state.visibleTools.includes(tool);
      return {
        visibleTools: isVisible
          ? state.visibleTools.filter((t) => t !== tool)
          : [...state.visibleTools, tool],
      };
    }),

  pinTool: (tool) =>
    set((state) => ({
      pinnedTools: [...state.pinnedTools, tool],
    })),

  unpinTool: (tool) =>
    set((state) => ({
      pinnedTools: state.pinnedTools.filter((t) => t !== tool),
    })),
}));
