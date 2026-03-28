export type ToolId =
  | "problemList"
  | "similarProblems"
  | "notes"
  | "solutionPanel"
  | "versionTimeline"
  | "aiSuggestions"
  | "teamChat"
  | "teamAiChat"
  | "privateAi"
  | "activityFeed";

export const TOOL_REGISTRY: Record<
  ToolId,
  {
    label: string;
    description: string;
    category: "core" | "ai" | "collab" | "planning" | "insight";
    mode?: "team" | "teamAi" | "private"; // added for ChatPanel
  }
> = {
  problemList: {
    label: "Problems",
    description: "View and switch between problems in this session.",
    category: "core",
  },

  similarProblems: {
    label: "Similar Problems",
    description: "AI‑retrieved similar problems from global knowledge.",
    category: "insight",
  },

  notes: {
    label: "Notes",
    description: "Personal or shared notes for this session.",
    category: "planning",
  },

  solutionPanel: {
    label: "Solution Panel",
    description: "View and edit the active solution.",
    category: "core",
  },

  versionTimeline: {
    label: "Version Timeline",
    description: "Track the evolution of the solution.",
    category: "core",
  },

  aiSuggestions: {
    label: "AI Suggestions",
    description: "AI‑generated improvements and insights.",
    category: "ai",
  },

  teamChat: {
    label: "Team Chat",
    description: "Human‑to‑human communication.",
    category: "collab",
    mode: "team",
  },

  teamAiChat: {
    label: "AI for Team",
    description: "Ask AI questions visible to the whole team.",
    category: "ai",
    mode: "teamAi",
  },

  privateAi: {
    label: "My AI",
    description: "Private AI assistant for personal help.",
    category: "ai",
    mode: "private",
  },

  activityFeed: {
    label: "Activity Feed",
    description: "Track changes and updates in the session.",
    category: "collab",
  },
};
