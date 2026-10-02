"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  Clock,
  Calendar,
  CheckCircle,
  AlertTriangle,
  Award,
  ChevronDown,
  ChevronUp,
  Printer,
  ArrowLeft,
  Loader2,
  ShieldCheck,
  HelpCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { FinalInterviewReport } from "@/types";
import ScoreGauge from "@/components/ScoreGauge";

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = params?.id as string;

  const [report, setReport] = useState<FinalInterviewReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [expandedQuestions, setExpandedQuestions] = useState<Record<number, boolean>>({});

  useEffect(() => {
    async function loadReport() {
      try {
        setIsLoading(true);
        const data = await api.getReport(interviewId);
        setReport(data);
      } catch (err: any) {
        // If report isn't synthesized yet, try triggering completion synthesis
        try {
          const compData = await api.completeInterview(interviewId);
          setReport(compData);
        } catch (compErr: any) {
          setErrorMsg("Could not load or synthesize interview report: " + (compErr.message || ""));
        }
      } finally {
        setIsLoading(false);
      }
    }

    if (interviewId) {
      loadReport();
    }
  }, [interviewId]);

  const toggleQuestion = (idx: number) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-brand-600 mb-4" />
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Synthesizing Final AI Report...</h2>
        <p className="text-sm text-slate-500 mt-1">Analyzing all responses, evaluating technical depth, and preparing recommendations.</p>
      </div>
    );
  }

  if (errorMsg || !report) {
    return (
      <div className="mx-auto max-w-xl px-4 py-16 text-center">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-8 dark:border-red-900 dark:bg-red-950/40">
          <AlertTriangle className="h-10 w-10 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Report Not Found</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{errorMsg || "Unable to retrieve report."}</p>
          <div className="mt-6">
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Home</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Header & Print actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            Official Interview Assessment
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
            Interview Report: {report.candidate_name}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            <Printer className="h-4 w-4" />
            <span>Print Report</span>
          </button>

          <Link
            href="/admin"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-brand-700"
          >
            <span>Admin Dashboard</span>
          </Link>
        </div>
      </div>

      {/* Candidate Metadata Strip */}
      <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 rounded-2xl bg-white dark:bg-slate-900 p-5 border border-slate-200 dark:border-slate-800 shadow-sm text-sm">
        <div>
          <span className="text-xs text-slate-400 block">Candidate</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">{report.candidate_name}</span>
        </div>
        <div>
          <span className="text-xs text-slate-400 block">Interview Date</span>
          <div className="flex items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-200">
            <Calendar className="h-3.5 w-3.5 text-brand-500" />
            <span>{report.interview_date}</span>
          </div>
        </div>
        <div>
          <span className="text-xs text-slate-400 block">Duration</span>
          <div className="flex items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-200">
            <Clock className="h-3.5 w-3.5 text-brand-500" />
            <span>{report.duration_minutes} mins</span>
          </div>
        </div>
        <div>
          <span className="text-xs text-slate-400 block">Questions Evaluated</span>
          <div className="flex items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-200">
            <FileText className="h-3.5 w-3.5 text-brand-500" />
            <span>{report.total_questions_asked} Questions</span>
          </div>
        </div>
      </div>

      {/* Main Score & Pillars Grid */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Overall Score Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 flex flex-col items-center justify-center text-center">
          <ScoreGauge score={report.overall_score} label="Overall Score" />

          <div className="mt-5 inline-flex items-center gap-2 rounded-full bg-slate-100 dark:bg-slate-800 px-4 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span>{report.recommendation || "Human Review Recommended"}</span>
          </div>

          <p className="text-[11px] text-slate-400 mt-2">
            Automated AI evaluation. Final hiring decision rests with human recruitment.
          </p>
        </div>

        {/* 5 Technical Pillars Breakdown */}
        <div className="md:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-4">
            Evaluation by Competency Pillar
          </h3>

          <div className="space-y-4">
            {[
              { label: "Technical Knowledge", val: report.category_scores.technical_knowledge },
              { label: "Project Understanding", val: report.category_scores.project_understanding },
              { label: "Problem Solving", val: report.category_scores.problem_solving },
              { label: "Communication Clarity", val: report.category_scores.communication_clarity },
              { label: "Resume Understanding", val: report.category_scores.resume_understanding },
            ].map((pillar, idx) => (
              <div key={idx}>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-slate-700 dark:text-slate-300">{pillar.label}</span>
                  <span className="text-brand-600 dark:text-brand-400">{pillar.val}/100</span>
                </div>
                <div className="h-2.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-600 to-sky-400 transition-all duration-1000 ease-out"
                    style={{ width: `${pillar.val}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Strengths & Areas for Improvement Grid */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2 text-sm font-bold text-emerald-600 dark:text-emerald-400 mb-4">
            <CheckCircle className="h-5 w-5" />
            <span>Key Strengths</span>
          </div>
          <ul className="space-y-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
            {report.strengths.map((st, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-emerald-500 font-bold">•</span>
                <span>{st}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Areas for Improvement */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2 text-sm font-bold text-amber-600 dark:text-amber-400 mb-4">
            <AlertTriangle className="h-5 w-5" />
            <span>Areas for Improvement</span>
          </div>
          <ul className="space-y-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
            {report.areas_for_improvement.map((area, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-amber-500 font-bold">•</span>
                <span>{area}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-2">
          Final Executive Summary
        </h3>
        <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          {report.final_summary}
        </p>
      </div>

      {/* Question-By-Question Detailed Analysis */}
      <div className="mt-8">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
          Question-by-Question Breakdown ({report.question_analyses.length} Questions)
        </h3>

        <div className="space-y-4">
          {report.question_analyses.map((qa, idx) => {
            const isExpanded = expandedQuestions[idx] ?? true; // expanded by default
            return (
              <div
                key={idx}
                className="rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden"
              >
                {/* Header */}
                <div
                  onClick={() => toggleQuestion(idx)}
                  className="flex items-center justify-between p-5 cursor-pointer bg-slate-50/50 hover:bg-slate-50 dark:bg-slate-800/40 dark:hover:bg-slate-800/80 transition"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-50 text-xs font-bold text-brand-600 dark:bg-brand-950 dark:text-brand-400">
                      {idx + 1}
                    </span>
                    <span className="font-semibold text-sm text-slate-900 dark:text-white">
                      {qa.question}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                        qa.score >= 80
                          ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400"
                          : qa.score >= 65
                          ? "bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400"
                          : "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400"
                      }`}
                    >
                      {qa.score}/100
                    </span>
                    {isExpanded ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="p-5 border-t border-slate-100 dark:border-slate-800 space-y-3.5 text-xs sm:text-sm">
                    {/* Candidate Spoken Answer */}
                    <div>
                      <span className="font-semibold text-slate-500 block mb-1">Spoken Candidate Response:</span>
                      <p className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl text-slate-700 dark:text-slate-300 italic border border-slate-200/60 dark:border-slate-800">
                        "{qa.candidate_answer}"
                      </p>
                    </div>

                    {/* Strengths & Missing Points */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                      <div className="rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 p-3 border border-emerald-100 dark:border-emerald-900/40">
                        <span className="font-semibold text-emerald-700 dark:text-emerald-400 block mb-1">
                          Demonstrated Strengths:
                        </span>
                        <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 text-xs">
                          {qa.strengths && qa.strengths.length > 0 ? (
                            qa.strengths.map((s, sidx) => <li key={sidx}>{s}</li>)
                          ) : (
                            <li>Covered fundamental points.</li>
                          )}
                        </ul>
                      </div>

                      <div className="rounded-xl bg-amber-50/50 dark:bg-amber-950/20 p-3 border border-amber-100 dark:border-amber-900/40">
                        <span className="font-semibold text-amber-700 dark:text-amber-400 block mb-1">
                          Missing or Omitted Points:
                        </span>
                        <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 text-xs">
                          {qa.missing_points && qa.missing_points.length > 0 ? (
                            qa.missing_points.map((m, midx) => <li key={midx}>{m}</li>)
                          ) : (
                            <li>No major omissions identified.</li>
                          )}
                        </ul>
                      </div>
                    </div>

                    {/* Evaluator Feedback */}
                    {qa.feedback && (
                      <div className="pt-2 text-xs text-slate-600 dark:text-slate-300">
                        <span className="font-semibold text-slate-700 dark:text-slate-200">Evaluator Feedback: </span>
                        {qa.feedback}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

