"use client";

import React from "react";

interface VoiceVisualizerProps {
  status: "connecting" | "speaking" | "listening" | "thinking" | "idle" | "error";
  mode: "ai" | "user";
}

export default function VoiceVisualizer({ status, mode }: VoiceVisualizerProps) {
  const isAi = mode === "ai";
  const isActive = isAi ? status === "speaking" : status === "listening";
  const isThinking = status === "thinking";

  return (
    <div className="flex items-center justify-center gap-1.5 h-12 px-4 py-2 rounded-xl bg-slate-900/5 dark:bg-slate-100/5 backdrop-blur-sm">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((bar) => {
        let heightClass = "h-2";
        let colorClass = isAi ? "bg-brand-500" : "bg-emerald-500";
        let animStyle = "";

        if (isActive) {
          // Dynamic pulsing heights
          const delays = ["0.1s", "0.2s", "0.3s", "0.15s", "0.25s", "0.05s", "0.35s", "0.2s"];
          animStyle = `animate-pulse`;
          const heights = ["h-6", "h-10", "h-8", "h-11", "h-7", "h-9", "h-5", "h-8"];
          heightClass = heights[bar - 1] || "h-6";
        } else if (isThinking) {
          colorClass = "bg-amber-500";
          heightClass = "h-3 animate-bounce";
        } else {
          colorClass = "bg-slate-300 dark:bg-slate-700";
          heightClass = "h-2";
        }

        return (
          <div
            key={bar}
            className={`w-1.5 rounded-full transition-all duration-300 ease-in-out ${heightClass} ${colorClass} ${animStyle}`}
            style={{ animationDelay: `${bar * 120}ms` }}
          />
        );
      })}
    </div>
  );
}

