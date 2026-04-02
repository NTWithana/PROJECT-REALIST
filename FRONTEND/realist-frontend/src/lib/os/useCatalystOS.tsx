// src/lib/os/useCatalystOS.ts
"use client";
import { createContext, useContext, useState, ReactNode } from "react";

type OSState = {
  mode: "global" | "focus";
  setMode: (m: "global" | "focus") => void;
};

const CatalystOSContext = createContext<OSState | null>(null);

export function CatalystOSProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<"global" | "focus">("global");

  return (
    <CatalystOSContext.Provider value={{ mode, setMode }}>
      {children}
    </CatalystOSContext.Provider>
  );
}

export function useCatalystOS() {
  const ctx = useContext(CatalystOSContext);
  if (!ctx) throw new Error("CatalystOS not mounted");
  return ctx;
}
