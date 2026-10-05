"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Mic, ShieldCheck, Users, Sun, Moon } from "lucide-react";

export default function Navbar() {
  const [isDark, setIsDark] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
    const hasDarkClass = document.documentElement.classList.contains("dark");
    setIsDark(hasDarkClass);
  }, []);

  const toggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    if (nextDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/95 transition-colors duration-150">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-90">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-sky-400 text-white shadow-md shadow-brand-500/20">
            <Mic className="h-5 w-5" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
              AI Voice Interviewer
            </div>
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Enterprise Mock & Technical Assessments
            </div>
          </div>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-3">
          <Link
            href="/upload"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <Mic className="h-4 w-4 text-brand-600 dark:text-brand-400" />
            <span>New Interview</span>
          </Link>

          <Link
            href="/admin"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <Users className="h-4 w-4 text-slate-500 dark:text-slate-400" />
            <span>Admin</span>
          </Link>

          {/* Theme Toggle Button */}
          {mounted && (
            <button
              onClick={toggleTheme}
              aria-label="Toggle Dark / Light Theme"
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition cursor-pointer"
              title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
            >
              {isDark ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-slate-600" />}
            </button>
          )}

          <div className="hidden md:flex items-center gap-1 text-xs text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800/60 px-2.5 py-1 rounded-full font-medium">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Secure Realtime Session</span>
          </div>
        </nav>
      </div>
    </header>
  );
}

