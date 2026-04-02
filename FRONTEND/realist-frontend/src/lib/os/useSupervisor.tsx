"use client";

import { create } from "zustand";

type SupervisorState = {
  summary: string | null;
  risks: string[] | null;
  nextActions: string[] | null;
  loading: boolean;

  setLoading: (v: boolean) => void;
  setSupervisorData: (data: {
    summary: string;
    risks: string[];
    nextActions: string[];
  }) => void;
};

export const useSupervisor = create<SupervisorState>((set) => ({
  summary: null,
  risks: null,
  nextActions: null,
  loading: false,

  setLoading: (v) => set({ loading: v }),

  setSupervisorData: (data) =>
    set({
      summary: data.summary,
      risks: data.risks,
      nextActions: data.nextActions,
    }),
}));
