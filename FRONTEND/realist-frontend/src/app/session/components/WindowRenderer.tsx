"use client";

import { useSessionUI } from "../state/useSession";
import { useState } from "react";
import type { WindowInstance } from "../state/useSession";

export default function WindowRenderer() {
  const { windows, closeWindow, focusWindow, activeWindowId } = useSessionUI();

  return (
    <>
      {windows.map((win) => (
        <FloatingWindow
          key={win.id}
          win={win}
          isActive={activeWindowId === win.id}
          onClose={() => closeWindow(win.id)}
          onFocus={() => focusWindow(win.id)}
        />
      ))}
    </>
  );
}

type FloatingWindowProps = {
  win: WindowInstance;
  isActive: boolean;
  onClose: () => void;
  onFocus: () => void;
};

function FloatingWindow({ win, isActive, onClose, onFocus }: FloatingWindowProps) {
  const [pos, setPos] = useState({ x: win.x, y: win.y });
  const [size] = useState({ w: win.width, h: win.height });

  const startDrag = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation(); // prevents conflict with onFocus

    const startX = e.clientX;
    const startY = e.clientY;

    const origX = pos.x;
    const origY = pos.y;

    const move = (ev: MouseEvent) => {
      setPos({
        x: origX + (ev.clientX - startX),
        y: origY + (ev.clientY - startY),
      });
    };

    const stop = () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", stop);
    };

    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", stop);
  };

  return (
    <div
      onMouseDown={onFocus}
      style={{
        top: pos.y,
        left: pos.x,
        width: size.w,
        height: size.h,
        zIndex: isActive ? 50 : 30,
      }}
      className={`fixed bg-[#0d0d12] border border-white/10 rounded-lg shadow-xl backdrop-blur-md transition-all ${
        isActive ? "ring-2 ring-cyan-500/40" : ""
      }`}
    >
      {/* Title Bar */}
      <div
        className="h-10 bg-white/5 border-b border-white/10 flex items-center justify-between px-3 cursor-move"
        onMouseDown={startDrag}
      >
        <span className="text-white/80 text-sm">{win.title}</span>
        <button
          onClick={onClose}
          className="text-white/40 hover:text-white/80"
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="p-4 overflow-auto h-[calc(100%-2.5rem)]">
        {win.content}
      </div>
    </div>
  );
}
