"use client";

import { motion, useAnimation, useInView } from "framer-motion";
import { useRef, useEffect } from "react";
import NeuronParticles from "@/components/ui/Particles";

export default function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const controls = useAnimation();

  useEffect(() => {
    if (isInView) {
      controls.start("visible");
    }
  }, [isInView, controls]);

const cardVariants: any = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.25,
      duration: 0.6,
      ease: "easeOut",
    },
  }),
};


  return (
    <section
      ref={ref}
      className="relative w-full py-24 px-6 bg-[#000000] text-white"
    >
    <NeuronParticles id="howItWorksparticles" className="fixed inset-0 z-0" />
    
    {/* Section Title */}
      <div className="text-center mb-16">
        <h2 className="text-4xl md:text-5xl font-bold text-white drop-shadow-[0_0_20px_rgba(76,201,240,0.4)]">
          How Realist Works With You
        </h2>
        <div className="mx-auto mt-4 h-[2px] w-24 bg-gradient-to-r from-[#4CC9F0] to-[#72EFDD] rounded-full" />
      </div>

      {/* Four-Pillar Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10 max-w-6xl mx-auto">
        {[
          {
            title: "Deep Intent Detection",
            text: "Realist understand what you need by analyzing context and patterns to nail your true goals with laser precision.",
          },
          {
            title: "Collective Intelligence",
            text: "AI agents acts with your team to debate and refine, delivering breakthroughs no single model can match.",
          },
          {
            title: "Adaptive Evolution",
            text: "Every interaction sharpens global hive mind and  it adapts to your style and gets smarter with you.",
          },
          {
            title: "Humans in Control",
            text: "We stay in full control — Realist Turbocharges our thinking without ever taking over.",
          },
        ].map((pillar, i) => (
          <motion.div
            key={i}
            custom={i}
            initial="hidden"
            animate={controls}
            variants={cardVariants}
            className="p-6 rounded-xl border border-[#4CC9F0]/30 bg-[#0A0A0A] shadow-[0_0_20px_rgba(76,201,240,0.15)] hover:shadow-[0_0_30px_rgba(76,201,240,0.3)] transition"
          >
            <h3 className="text-xl font-semibold text-[#4CC9F0] mb-3">
              {pillar.title}
            </h3>
            <p className="text-[#A8DADC] leading-relaxed">{pillar.text}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
