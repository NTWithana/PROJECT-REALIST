"use client";

import { useEffect, useState } from "react";
import { Orbitron } from "next/font/google";
import NeuronParticles from "@/components/ui/Particles";
import Image from "next/image";

import GlobalSearchPanel from "@/components/hub/GlobalSearchPanel";
import SessionsPanel from "@/components/hub/YourSessions";
import TrendingPanel from "@/components/hub/TrendingPanel";
import StatsPanel from "@/components/hub/StatsPanel";

const orbitron = Orbitron({
  subsets: ["latin"],
  weight: ["400", "700"],
});

export default function GlobalHub() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="relative min-h-screen bg-black text-white overflow-hidden">

      <NeuronParticles id="hubParticles" className="fixed inset-0 z-0" />

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(76,201,240,0.15),transparent_70%)] pointer-events-none" />

      <header className="relative z-10 w-full border-b border-white/10 bg-black/40 backdrop-blur">
        <div className="max-w-7xl mx-auto flex items-center justify-between py-4 px-6">
          <div className="flex items-center gap-3">
            <Image
              src="/Realistlogo.png"
              alt="Realist Logo"
              width={40}
              height={40}
              className="drop-shadow-[0_0_20px_rgba(76,201,240,0.8)]"
            />
            <span className="text-xl font-bold tracking-wider text-white/90">
              REALIST
            </span>
          </div>

          <div className="flex items-center gap-4">
            <button className="px-4 py-1.5 border border-white/20 rounded-md hover:bg-white/10 transition">
              Login
            </button>
            <button className="px-4 py-1.5 bg-gradient-to-r from-[#4CC9F0] to-[#72EFDD] text-black font-semibold rounded-md shadow-[0_0_20px_rgba(76,201,240,0.7)] hover:scale-105 transition">
              Create Account
            </button>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-12 space-y-14">

        {mounted && (
          <div className="text-center space-y-3">
            <h1
              className={`${orbitron.className} text-4xl md:text-5xl font-bold tracking-wide text-white`}
            >
              {"REALIST GLOBAL HUB".split("").map((char, i) => (
                <span
                  key={i}
                  className="title-letter inline-block"
                  style={{ animationDelay: `${i * 0.04}s` }}
                >
                  {char === " " ? "\u00A0" : char}
                </span>
              ))}
            </h1>

            <p className="text-white/40 text-sm fade-slide-up delay-[1200ms]">
              Your global intelligence layer — privacy‑safe, insight‑rich.
            </p>
          </div>
        )}

        <section>
          <GlobalSearchPanel />
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10">

          <div className="fade-slide-up bg-white/5 border border-white/10 rounded-lg p-4 backdrop-blur shadow-[0_0_20px_rgba(76,201,240,0.15)]">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">Your Sessions</h2>
              <button className="px-3 py-1 bg-gradient-to-r from-[#4CC9F0] to-[#72EFDD] text-black text-sm font-semibold rounded-md shadow-[0_0_15px_rgba(76,201,240,0.7)] hover:scale-105 transition">
                New Session
              </button>
            </div>
            <SessionsPanel />
          </div>

          <div className="fade-slide-up bg-white/5 border border-white/10 rounded-lg p-4 backdrop-blur shadow-[0_0_20px_rgba(76,201,240,0.15)]">
            <h2 className="text-lg font-semibold mb-3">Global Trends</h2>
            <TrendingPanel />
          </div>

          <div className="fade-slide-up bg-white/5 border border-white/10 rounded-lg p-4 backdrop-blur shadow-[0_0_20px_rgba(76,201,240,0.15)]">
            <h2 className="text-lg font-semibold mb-3">Global Stats</h2>
            <StatsPanel />
          </div>

        </section>
      </main>
    </div>
  );
}
