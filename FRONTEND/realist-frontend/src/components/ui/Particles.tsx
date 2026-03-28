"use client";

import { useCallback } from "react";
import Particles from "react-tsparticles";
import type { Engine } from "tsparticles-engine";
import { loadFull } from "tsparticles";

export default function NeuronParticles({
  className,
  id,
}: {
  className?: string;
  id?: string;
}) {
  const init = useCallback(async (engine: Engine) => {
    await loadFull(engine);
  }, []);

  return (
    <Particles
      id={id}
      className={className}
      init={init}
      options={{
        background: { color: "transparent" },
        fpsLimit: 60,

        interactivity: {
          events: {
            onHover: { enable: true, mode: "grab" },
            resize: true,
          },
          modes: {
            grab: {
              distance: 180,
              links: { opacity: 0.7 },
            },
          },
        },

        particles: {
          number: { value: 60 },
          color: { value: "#4CC9F0" },

          links: {
            enable: true,
            color: "#4CC9F0",
            distance: 140,
            opacity: 0.4,
            width: 1,
          },

          move: {
            enable: true,
            speed: 0.6,
            direction: "none",
            outModes: "bounce",
          },

          size: { value: 2 },
          opacity: { value: 0.6 },
        },

        detectRetina: true,
        fullScreen: false,
      }}
    />
  );
}
