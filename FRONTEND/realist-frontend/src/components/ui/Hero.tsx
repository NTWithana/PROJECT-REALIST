"use client";

import { Orbitron } from "next/font/google";
import NeuronParticles from "@/components/ui/Particles";
import Image from "next/image";

const orbitron = Orbitron({
  subsets: ["latin"],
  weight: ["400", "700"],
});

export default function Hero() {
  return (
   <section className="relative flex flex-col items-center justify-center min-h-screen px-6 text-center bg-[#000000] overflow-hidden">


      {/* Neuron Particle Network */}
    <NeuronParticles id="heroParticles" className="fixed inset-0 z-0" />

      {/* Blue Glow Aura */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(76,201,240,0.18),transparent_70%)] pointer-events-none" />

      {/* Logo */}
      <div className="relative z-10 mb-6">
        <Image
        src="/Realistlogo.png"
        alt="Realist Logo"
        width={60}
        height={60}
        className="drop-shadow-[0_0_25px_rgba(76,201,240,0.8)]"
/>

      </div>

      {/* Micro Tagline */}
      <p className="relative z-10 text-sm tracking-widest text-[#72EFDD] uppercase mb-4">
        Developed by Variable X
      </p>

      {/* Main Headline */}
      <h1
        className={`${orbitron.className} relative z-10 text-5xl md:text-7xl font-bold text-white leading-tight drop-shadow-[0_0_25px_rgba(76,201,240,0.4)]`}
      >
        Beyond Artificial Intelligence!<br />
        <span className="text-[#4CC9F0]">This is Us — Amplified!</span>
      </h1>

      {/* Subheadline */}
      <p className="relative z-10 mt-6 text-xl md:text-2xl text-[#A8DADC] max-w-2xl leading-relaxed">
        Humans with Artificial Intelligence - One shared mind, infinite possibilities.
      </p>

      {/* Supporting Line */}
      <p className="relative z-10 mt-4 text-lg text-[#89C2D9] max-w-xl">
        Solve Problems. Create Solutions. Evolve Together.
      </p>

      {/* CTA Buttons */}
      <div className="relative z-10 mt-10 flex flex-col sm:flex-row gap-4">
        <button className="px-8 py-3 rounded-full bg-gradient-to-r from-[#4CC9F0] to-[#72EFDD] text-black font-semibold shadow-[0_0_25px_rgba(76,201,240,0.7)] hover:scale-105 transition">
          ENTER GLOBAL HUB
        </button>

        <button className="px-8 py-3 rounded-full bg-gradient-to-r from-[#4CC9F0] to-[#72EFDD] text-black font-semibold shadow-[0_0_25px_rgba(76,201,240,0.7)] hover:scale-105 transition">
          CREAT ACCOUNT
        </button>
      </div>
    </section>
  );
}