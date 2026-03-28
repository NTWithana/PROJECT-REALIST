"use client";

import { motion } from "framer-motion";
import NeuronParticles from "@/components/ui/Particles";

export default function WhyDifferent() {
  return (
    <section className="relative w-full py-24 px-6 bg-black text-white overflow-hidden">

      {/* Particles Behind */}
      <NeuronParticles id="whyDifferentParticles" className="fixed inset-0 z-0" />

      <div className="relative z-10 max-w-6xl mx-auto">

        {/* Title */}
        <h2 className="text-center text-4xl md:text-5xl font-bold drop-shadow-[0_0_20px_rgba(76,201,240,0.4)] mb-16">
          Why Realist Is Not a Traditional AI Tool
        </h2>

        {/* Two Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">

          {/* Traditional AI */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="p-8 rounded-2xl bg-[#0a0a0a] border border-[#1f1f1f] shadow-[0_0_25px_rgba(0,0,0,0.6)]"
          >
            <h3 className="text-2xl font-semibold text-[#ef476f] mb-4">
              Traditional AI Tools
            </h3>
            <ul className="space-y-3 text-[#bdbdbd] text-lg">
              <li>• One model, one perspective</li>
              <li>• Works alone — no collaboration</li>
              <li>• Doesn’t understand your true intent</li>
              <li>• No memory across sessions</li>
              <li>• No evolving solutions</li>
              <li>• No versioning or refinement</li>
              <li>• No shared knowledge</li>
              <li>• No teamwork or co-solving</li>
              <li>• Doesn’t learn from your judgment</li>
            </ul>
          </motion.div>

          {/* Realist */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="p-8 rounded-2xl bg-[#0d1b2a] border border-[#4cc9f0] shadow-[0_0_35px_rgba(76,201,240,0.4)]"
          >
            <h3 className="text-2xl font-semibold text-[#4cc9f0] mb-4">
              Realist — A New Kind of Intelligence
            </h3>
            <ul className="space-y-3 text-[#d9faff] text-lg">
              <li>• A hive of humens + specialized agents </li>
              <li>• Thinks with you, not at you</li>
              <li>• Understands your intent</li>
              <li>• Remembers your work across sessions</li>
              <li>• Evolves solutions over time</li>
              <li>• Full editing, branching, versioning</li>
              <li>• Global shared intelligence</li>
              <li>• Multi-person collaboration</li>
              <li>• Learns from your judgment</li>
            </ul>
          </motion.div>
        </div>

        {/* Smooth Word-by-Word Reveal + Shimmer */}
        <motion.div
          className="mt-20 flex flex-wrap justify-center text-center text-3xl md:text-5xl font-bold shimmer"
        >
          {[
            "This",
            "is",
            "the",
            "Future.",
            "We",
            "don’t",
            "replace",
            "humans.",
            "We",
            "upgrade",
            "them!"
          ].map((word, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, y: 14, scale: 0.94 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              transition={{
                duration: 0.55,
                delay: i * 0.12,
                ease: [0.16, 1, 0.3, 1]
              }}
              className={
                word === "them!"
                  ? "text-[#4CC9F0] ml-2"
                  : "text-white ml-2"
              }
            >
              {word}
            </motion.span>
          ))}
        </motion.div>

        {/* Human × AI Fusion */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.5 }}
          className="mt-10 max-w-3xl mx-auto text-lg md:text-xl text-[#A8DADC] leading-relaxed text-center"
        >
          Realist is the fusion of human critical thinking, creativity, and judgment
          with the speed, scale, and pattern-recognition of advanced LLMs.
          Not man vs machine — but <span className="text-[#4CC9F0] font-semibold">man amplified by machine</span>.
          A shared intelligence where knowledge grows globally, and every user strengthens the hive.
        </motion.p>

      </div>
    </section>
  );
}
