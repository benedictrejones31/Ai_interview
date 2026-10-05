import Link from "next/link";
import { Mic, FileText, Sparkles, BrainCircuit, ShieldCheck, CheckCircle2, ArrowRight } from "lucide-react";

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* Background Decorative Gradient Blobs */}
      <div className="pointer-events-none absolute -top-40 right-0 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80">
        <div className="relative left-[calc(50%+11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-brand-400 to-sky-200 opacity-30 sm:left-[calc(50%+30rem)] sm:w-[72.1875rem]" />
      </div>

      {/* Hero Section */}
      <section className="relative px-6 pt-16 pb-20 sm:px-8 sm:pt-24 lg:px-12 text-center max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-50 border border-brand-200/80 text-brand-700 text-xs font-semibold tracking-wide uppercase shadow-sm dark:bg-brand-950/40 dark:border-brand-800/60 dark:text-brand-300 mb-6">
          <Sparkles className="h-4 w-4" />
          <span>Next-Generation Technical Interviews</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.15]">
          AI Voice Interviewer
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto font-normal leading-relaxed text-balance">
          Upload your resume and complete a personalized AI-powered voice interview based on your actual skills, projects, education, and engineering experience.
        </p>

        {/* Call to Action Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/upload"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 rounded-xl bg-brand-600 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-brand-500/25 transition-all hover:bg-brand-700 hover:shadow-brand-500/35 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 active:scale-[0.98]"
          >
            <Mic className="h-5 w-5" />
            <span>Start Voice Interview</span>
            <ArrowRight className="h-4 w-4 ml-1" />
          </Link>

          <Link
            href="/admin"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-6 py-4 text-base font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            <span>View Candidate Reports</span>
          </Link>
        </div>

        {/* Prerequisites Badge Row */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-600 dark:text-slate-300 font-medium">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <span>PDF Resume Required (&le; 10MB)</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <span>Microphone & Camera Enabled</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <span>10 Core Questions</span>
          </div>
        </div>
      </section>

      {/* How it Works / 4-Step Process Section */}
      <section className="bg-slate-100/60 dark:bg-slate-900/60 py-20 border-y border-slate-200/80 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              How The AI Voice Interview Works
            </h2>
            <p className="mt-3 text-slate-600 dark:text-slate-300 text-sm sm:text-base">
              A seamless, natural simulation of an actual senior engineering hiring interview.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Step 1 */}
            <div className="relative rounded-2xl bg-white p-7 shadow-sm border border-slate-200/80 dark:bg-slate-800/80 dark:border-slate-700 flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400 mb-5">
                  <FileText className="h-6 w-6" />
                </div>
                <div className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 mb-1">
                  Step 1
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  Upload Resume
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  Provide your PDF resume. Our PyMuPDF engine extracts and validates your skills, projects, and work history.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative rounded-2xl bg-white p-7 shadow-sm border border-slate-200/80 dark:bg-slate-800/80 dark:border-slate-700 flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400 mb-5">
                  <BrainCircuit className="h-6 w-6" />
                </div>
                <div className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 mb-1">
                  Step 2
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  Tailored Questions
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  AI analyzes your profile to craft 10 foundational technical questions tailored directly to your projects, architectures, and listed stack.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative rounded-2xl bg-white p-7 shadow-sm border border-slate-200/80 dark:bg-slate-800/80 dark:border-slate-700 flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400 mb-5">
                  <Mic className="h-6 w-6" />
                </div>
                <div className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 mb-1">
                  Step 3
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  Live Voice Dialogue
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  AI interviewer speaks instructions and questions aloud in real-time. You reply through your microphone, with adaptive follow-ups.
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="relative rounded-2xl bg-white p-7 shadow-sm border border-slate-200/80 dark:bg-slate-800/80 dark:border-slate-700 flex flex-col justify-between">
              <div>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400 mb-5">
                  <ShieldCheck className="h-6 w-6" />
                </div>
                <div className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-1">
                  Step 4
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  Objective Report
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  Instant evaluation across 5 technical pillars with strengths, missing points, and candidate score stored in PostgreSQL.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

