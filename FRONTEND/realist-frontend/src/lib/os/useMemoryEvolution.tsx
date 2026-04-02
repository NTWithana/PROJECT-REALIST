"use client";

import { create } from "zustand";
import { ChatSignal } from "./types/ChatSignal";

type MemoryState = {
  signals: ChatSignal[];
  addSignals: (s: ChatSignal[]) => void;
};

export const useMemoryEvolution = create<MemoryState>((set) => ({
  signals: [],
  addSignals: (s) =>
    set((state) => ({
      signals: [...state.signals, ...s],
    })),
}));
