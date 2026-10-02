"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  Search,
  FileText,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ShieldAlert,
  Loader2,
  Award,
} from "lucide-react";
import { api } from "@/lib/api";
import { AdminInterviewSummary } from "@/types";

export default function AdminPage() {
  const [interviews, setInterviews] = useState<AdminInterviewSummary[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    async function loadAdminData() {
      try {
        setIsLoading(true);
        const data = await api.getAdminInterviews();
        setInterviews(data);
      } catch (err: any) {
        setErrorMsg("Failed to load interviews. " + (err.message || ""));
      } finally {
        setIsLoading(false);
      }
    }
    loadAdminData();
  }, []);

  const filteredInterviews = interviews.filter((it) =>
    it.candidate_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    it.resume_filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const completedCount = interviews.filter((it) => it.status === "completed").length;
  const avgScore =
    completedCount > 0
      ? Math.round(
          interviews
            .filter((it) => it.overall_score !== null && it.overall_score !== undefined)
            .reduce((acc, it) => acc + (it.overall_score || 0), 0) / completedCount
        )
      : 0;

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      {/* Top Banner & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            Recruitment Portal
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
            Candidate Interview Evaluations
          </h1>
        </div>

        <Link
          href="/upload"
          className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700 transition"
        >
          <span>Conduct New Interview</span>
        </Link>
      </div>

      {/* Security & Production Guidance Notice (Section 34) */}
      <div className="mt-6 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50/80 p-4 text-xs text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
        <ShieldAlert className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
        <div>
          <span className="font-semibold">Enterprise Security Note: </span>
          In production environments, restrict this recruiter view behind SSO/OAuth or RBAC authentication before deploying with live confidential candidate resumes.
        </div>
      </div>

      {/* Metrics Row */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Interviews</span>
            <Users className="h-5 w-5 text-brand-500" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-slate-900 dark:text-white">
            {interviews.length}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Completed Sessions</span>
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-slate-900 dark:text-white">
            {completedCount}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Avg Technical Score</span>
            <Award className="h-5 w-5 text-brand-500" />
          </div>
          <div className="mt-2 text-2xl font-extrabold text-slate-900 dark:text-white">
            {avgScore > 0 ? `${avgScore}/100` : "N/A"}
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="mt-8 flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search candidate name or file..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:border-brand-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Candidates Table (Section 34) */}
      <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
          </div>
        ) : filteredInterviews.length === 0 ? (
          <div className="p-12 text-center text-sm text-slate-500">
            No interview records found. Upload a resume to conduct your first voice interview.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="border-b border-slate-200 bg-slate-50/80 text-xs font-bold uppercase tracking-wider text-slate-500 dark:border-slate-800 dark:bg-slate-800/60 dark:text-slate-400">
                <tr>
                  <th className="px-6 py-4">Candidate</th>
                  <th className="px-6 py-4">Resume File</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Questions Answered</th>
                  <th className="px-6 py-4">Overall Score</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                {filteredInterviews.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 font-semibold text-slate-900 dark:text-white">
                      {item.candidate_name}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {item.resume_filename}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
                          item.status === "completed"
                            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
                            : item.status === "in_progress"
                            ? "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400 border border-blue-200 dark:border-blue-800"
                            : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {item.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      {item.completed_questions} / {item.total_questions}
                    </td>
                    <td className="px-6 py-4">
                      {item.overall_score !== null && item.overall_score !== undefined ? (
                        <span
                          className={`font-bold px-2 py-0.5 rounded text-xs ${
                            item.overall_score >= 80
                              ? "text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/50"
                              : item.overall_score >= 65
                              ? "text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-950/50"
                              : "text-amber-700 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/50"
                          }`}
                        >
                          {Math.round(item.overall_score)}/100
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">In Progress</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {item.status === "completed" ? (
                        <Link
                          href={`/report/${item.id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
                        >
                          <span>View Report</span>
                          <ArrowUpRight className="h-3.5 w-3.5" />
                        </Link>
                      ) : (
                        <Link
                          href={`/interview/${item.id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400"
                        >
                          <span>Resume Interview</span>
                          <ArrowUpRight className="h-3.5 w-3.5" />
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

