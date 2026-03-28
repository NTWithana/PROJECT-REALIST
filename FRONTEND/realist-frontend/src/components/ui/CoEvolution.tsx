"use client";

import { motion, AnimatePresence, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import NeuronParticles from "@/components/ui/Particles";






export default function CoEvolution() {
  const centerText = "AI + Humans > Alone";

  const words = [
    "AMPLIFY",
    "TOGETHER",
    "THINK",
    "SOLVE",
    "COLLABORATE",
    "EVOLVE",
    "HUMANS",
    "ARTIFICIAL INTELLIGENCE",
    "HIVE MIND",
    "COLLECTIVE INTELLIGENCE",
    "THE FUTURE",
    "NEXT - GENERATION",
  ];

  const CHANNELS = 3;

  const [slots, setSlots] = useState(
    Array.from({ length: CHANNELS }).map(() => ({
      word: "",
      pos: { x: 0, y: 0 },
      visible: false,
    }))
  );

  const sectionRef = useRef<HTMLDivElement | null>(null);
  const inView = useInView(sectionRef, { once: true, margin: "-100px" });

 
  // SAFE POSITION GENERATOR
  

  const generatePosition = (existing: { x: number; y: number }[]) => {
    const safeRadius = 340;
    const minDistance = 180;
    const maxRadius = 460;

    let x = 0;
    let y = 0;
    let attempts = 0;

    do {
      const angle = Math.random() * Math.PI * 2;
      const radius = safeRadius + Math.random() * (maxRadius - safeRadius);

      x = Math.cos(angle) * radius;
      y = Math.sin(angle) * radius;

      // Avoid main text vertical band
      if (y > -80 && y < 120) continue;

      // Avoid bottom text
      if (y > 200) continue;

      attempts++;
      if (attempts > 25) break;
    } while (
      existing.some((p) => Math.hypot(p.x - x, p.y - y) < minDistance)
    );

    return { x, y };
  };

 
  // MULTI-WORD FLOATING SYSTEM
 

  useEffect(() => {
    const timers = slots.map((slot, i) =>
      setInterval(() => {
        setSlots((prev) => {
          const updated = [...prev];

          const usedWords = updated.map((s) => s.word);
          const available = words.filter((w) => !usedWords.includes(w));

          const newWord =
            available[Math.floor(Math.random() * available.length)];

          const positions = updated.map((s) => s.pos);
          const newPos = generatePosition(positions);

          updated[i] = {
            word: newWord,
            pos: newPos,
            visible: true,
          };

          return updated;
        });
      }, 2000 + i * 500)
    );

    return () => timers.forEach(clearInterval);
  }, []);

  // RENDER
 

  return (
<section
  ref={sectionRef}
  className="relative flex flex-col items-center justify-center min-h-screen px-6 text-center bg-[#000000] overflow-hidden"
>
  <NeuronParticles id="coEvolutionParticles" className="fixed inset-0 z-0" />


  <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_center,rgba(76,201,240,0.18),transparent_70%)] pointer-events-none" />



      {/* Main Center Text */}
      <TypewriterMain inView={inView} text={centerText} />

      {/* MULTIPLE FLOATING WORDS */}
      {slots.map((slot, i) => (
        <AnimatePresence key={i}>
          {slot.visible && (
            <motion.div
              key={slot.word + i}
              initial={{ opacity: 0, x: slot.pos.x, y: slot.pos.y }}
              animate={{ opacity: 1, x: slot.pos.x, y: slot.pos.y }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="absolute text-3xl md:text-4xl font-light text-[#A8DADC] z-10"
              style={{ textShadow: "0 0 18px rgba(76,201,240,0.7)" }}
            >
              {slot.word}
            </motion.div>
          )}
        </AnimatePresence>
      ))}

      {/* Supporting Line */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={inView ? { opacity: 1 } : {}}
        transition={{ duration: 1.5 }}
        className="absolute bottom-10 text-center text-[#6FC7E8] opacity-90 text-lg md:text-xl z-10"
      >
        Intelligence multiplies when humans and AI work together — not independently.
      </motion.div>
    </section>
  );
}


// TYPEWRITER MAIN TEXT


function TypewriterMain({ inView, text }: { inView: boolean; text: string }) {
  const [len, setLen] = useState(0);

  useEffect(() => {
    if (!inView) return;
    if (len >= text.length) return;

    const t = setTimeout(() => setLen((l) => l + 1), 70);
    return () => clearTimeout(t);
  }, [inView, len, text.length]);

  return (
    <div
      className="absolute text-4xl md:text-6xl lg:text-7xl font-bold text-[#4CC9F0] font-[Orbitron] whitespace-nowrap z-10"
      style={{
        textShadow:
          "0 0 35px rgba(76,201,240,1), 0 0 65px rgba(76,201,240,0.8)",
      }}
    >
      {text.slice(0, len)}
      <span className="border-r-4 border-[#4CC9F0] ml-1 animate-pulse" />
    </div>
  );
}
