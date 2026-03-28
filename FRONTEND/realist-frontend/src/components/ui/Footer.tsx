"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import NeuronParticles from "@/components/ui/Particles";
import Image from "next/image";

export default function FinalFooter() {
  const [open, setOpen] = useState<string | null>(null);

  const toggle = (key: string) => {
    setOpen(open === key ? null : key);
  };

  return (
    <section className="relative w-full py-24 px-6 bg-black text-white overflow-hidden">

      {/* Particles Behind */}
      <NeuronParticles id="footerParticles" className="fixed inset-0 z-0" />

      <div className="relative z-10 max-w-5xl mx-auto text-center">

        {/* Cinematic Philosophy Line */}
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="text-3xl md:text-5xl font-bold mb-10 drop-shadow-[0_0_25px_rgba(76,201,240,0.6)]"
        >
          Intelligence Evolves When We Evolve Together.
        </motion.h2>

        {/* Brand Identity Line */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.4 }}
          className="text-lg md:text-xl text-[#A8DADC] mb-16"
        >
          Built by humans. Amplified by AI. Powered by Realist.
        </motion.p>

        {/* Logo */}
        <div className="flex justify-center mb-10">
          <Image
            src="/Realistlogo.png"
            alt="Realist Logo"
            width={80}
            height={80}
            className="opacity-90 hover:opacity-100 transition"
          />
        </div>

        {/* Expandable Sections */}
        <div className="space-y-4 text-left max-w-xl mx-auto">

          {/* Item Template */}
          {[
            {
              key: "about",
              title: "About Realist",
              content:
                "Realist is a collaborative, collective intelligence System for problem solving designed to amplify human judgment, creativity, and problem‑solving through a global hive of Humens and Artificial Intelligence.",
            },
            {
              key: "philosophy",
              title: "Philosophy",
              content:
                "We believe Productivity and Precision multiplies when humans and AI work and evolve together not independently. Realist is built on co‑evolution, not automation.",
            },
            {
              key: "branding",
              title: "Branding",
              content:
                "Use the Realist logo with respect to its neon‑sci‑fi identity. Avoid distortion, recoloring, or low‑contrast backgrounds.",
            },
            {
              key: "privacy",
              title: "Privacy",
              content:
                "Realist does not collect personal data at this stage. As the platform evolves, this page will be updated.",
            },
          ].map((item) => (
            <div key={item.key} className="border border-[#1f1f1f] rounded-xl p-4 bg-[#0a0a0a]/60">
              <button
                onClick={() => toggle(item.key)}
                className="w-full flex justify-between items-center text-lg font-semibold text-[#4CC9F0]"
              >
                {item.title}
                <span className="text-white">{open === item.key ? "−" : "+"}</span>
              </button>

              {open === item.key && (
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                  className="mt-3 text-[#A8DADC] leading-relaxed"
                >
                  {item.content}
                </motion.p>
              )}
            </div>
          ))}
        </div>

        {/* Footer Links */}
        <div className="mt-16 flex flex-wrap justify-center gap-6 text-lg">

          <a href="/login" className="text-[#4CC9F0] hover:text-white transition">
            Login
          </a>

          <a href="/register" className="text-[#4CC9F0] hover:text-white transition">
            Sign Up
          </a>

          <a href="/hub" className="text-[#4CC9F0] hover:text-white transition">
            Global Hub
          </a>

          <a
            href="mailto:yourgmail@gmail.com"
            className="text-[#4CC9F0] hover:text-white transition"
          >
            Gmail
          </a>

          <a
            href="https://linkedin.com/in/yourprofile"
            target="_blank"
            className="text-[#4CC9F0] hover:text-white transition"
          >
            LinkedIn
          </a>

          <a
            href="https://github.com/yourgithub"
            target="_blank"
            className="text-[#4CC9F0] hover:text-white transition"
          >
            GitHub
          </a>
        </div>

        {/* Bottom Line */}
        <p className="mt-10 text-sm text-[#6c757d]">
          © {new Date().getFullYear()} Realist. All rights reserved.
        </p>
      </div>
    </section>
  );
}

