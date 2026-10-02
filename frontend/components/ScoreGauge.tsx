"use client";

import React from "react";

interface ScoreGaugeProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export default function ScoreGauge({
  score,
  size = 140,
  strokeWidth = 12,
  label = "Overall Score",
}: ScoreGaugeProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const clampedScore = Math.max(0, Math.min(100, score));
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  let color = "#0b8de9"; // brand blue
  let textColor = "text-brand-600";
  if (clampedScore >= 80) {
    color = "#10b981"; // emerald
    textColor = "text-emerald-600";
  } else if (clampedScore >= 65) {
    color = "#3b82f6"; // blue
    textColor = "text-blue-600";
  } else {
    color = "#f59e0b"; // amber
    textColor = "text-amber-600";
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="h-full w-full -rotate-90 transform" viewBox={`0 0 ${size} ${size}`}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-100 dark:text-slate-800"
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center score display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-extrabold tracking-tight ${textColor}`}>
            {clampedScore}
          </span>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            out of 100
          </span>
        </div>
      </div>
      {label && <span className="mt-2 text-sm font-medium text-slate-600 dark:text-slate-300">{label}</span>}
    </div>
  );
}

