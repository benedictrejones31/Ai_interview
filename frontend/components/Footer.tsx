import { Shield, Sparkles, Cpu } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white py-8 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-brand-600" />
          <span className="font-semibold text-slate-800 dark:text-slate-200">AI Voice Interviewer</span>
          <span>&copy; {new Date().getFullYear()} Enterprise Edition</span>
        </div>

        <div className="flex flex-wrap items-center gap-6 text-xs">
          <span className="flex items-center gap-1.5">
            <Shield className="h-3.5 w-3.5 text-emerald-500" />
            Backend Ephemeral Credential Security
          </span>
          <span className="flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-brand-500" />
            OpenAI Realtime Voice & PyMuPDF Powered
          </span>
        </div>
      </div>
    </footer>
  );
}

