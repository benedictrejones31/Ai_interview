"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileText,
  AlertCircle,
  Loader2,
  CheckCircle,
  Briefcase,
  GraduationCap,
  FolderGit2,
  Sparkles,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Candidate, Question } from "@/types";

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState<string>("");

  // Extracted confirmation state
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);

  const handleFileSelection = (file: File) => {
    setErrorMsg(null);

    // Validate type
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      setErrorMsg("Invalid file format. Only PDF files are supported.");
      setSelectedFile(null);
      return;
    }

    // Validate size (10 MB)
    const maxBytes = 10 * 1024 * 1024;
    if (file.size > maxBytes) {
      setErrorMsg(`File size exceeds 10 MB limit (${(file.size / (1024 * 1024)).toFixed(2)} MB).`);
      setSelectedFile(null);
      return;
    }

    if (file.size === 0) {
      setErrorMsg("The selected PDF file is empty (0 bytes).");
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleUploadAndProcess = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setErrorMsg(null);
    setProcessingStage("Extracting text with PyMuPDF...");

    try {
      setTimeout(() => {
        setProcessingStage("Analyzing candidate profile with OpenAI...");
      }, 1200);

      setTimeout(() => {
        setProcessingStage("Generating 10–15 tailored interview questions...");
      }, 3000);

      const response = await api.uploadResume(selectedFile);
      setCandidate(response.candidate);
      setInterviewId(response.interview_id);
      setQuestions(response.questions);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to upload or analyze resume. Please verify the backend is running.");
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStartInterview = () => {
    if (interviewId) {
      router.push(`/interview/${interviewId}`);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
      {/* If profile is extracted, show Confirmation Screen (Step 4) */}
      {candidate && interviewId ? (
        <div className="space-y-8 animate-fadeIn">
          {/* Top Banner */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-6 dark:border-emerald-900/60 dark:bg-emerald-950/30">
            <div className="flex items-start gap-4">
              <div className="rounded-xl bg-emerald-500 p-2 text-white shadow-md">
                <CheckCircle className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                  Profile Extracted & Questions Ready
                </h2>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                  We synthesized your background and prepared {questions.length} personalized questions for your mock interview.
                </p>
              </div>
            </div>
          </div>

          {/* Profile Overview Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="border-b border-slate-100 pb-5 dark:border-slate-800">
              <div className="text-xs font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                Candidate Profile
              </div>
              <h1 className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
                {candidate.name}
              </h1>
              {candidate.profile.summary && (
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                  {candidate.profile.summary}
                </p>
              )}
            </div>

            {/* Skills */}
            {candidate.profile.skills && candidate.profile.skills.length > 0 && (
              <div className="pt-5">
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                  Verified Skills & Technologies
                </h3>
                <div className="flex flex-wrap gap-2">
                  {candidate.profile.skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="rounded-lg bg-brand-50 border border-brand-200 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-950/60 dark:border-brand-800 dark:text-brand-300"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Projects & Experience Grid */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-slate-100 dark:border-slate-800">
              {/* Projects */}
              <div>
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
                  <FolderGit2 className="h-4 w-4 text-brand-500" />
                  <span>Key Projects</span>
                </div>
                {candidate.profile.projects && candidate.profile.projects.length > 0 ? (
                  <div className="space-y-3">
                    {candidate.profile.projects.slice(0, 3).map((proj, idx) => (
                      <div
                        key={idx}
                        className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3.5 dark:border-slate-800 dark:bg-slate-800/40"
                      >
                        <div className="font-medium text-slate-900 dark:text-white text-sm">
                          {proj.title}
                        </div>
                        {proj.description && (
                          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                            {proj.description}
                          </div>
                        )}
                        {proj.technologies && proj.technologies.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {proj.technologies.map((t, tidx) => (
                              <span key={tidx} className="text-[10px] bg-slate-200/80 dark:bg-slate-700 px-1.5 py-0.5 rounded text-slate-700 dark:text-slate-300">
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">No project details extracted.</p>
                )}
              </div>

              {/* Experience & Education */}
              <div className="space-y-6">
                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
                    <Briefcase className="h-4 w-4 text-brand-500" />
                    <span>Experience Highlights</span>
                  </div>
                  {candidate.profile.experience && candidate.profile.experience.length > 0 ? (
                    <div className="space-y-2">
                      {candidate.profile.experience.slice(0, 2).map((exp, idx) => (
                        <div key={idx} className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-lg border border-slate-200/60 dark:border-slate-800">
                          <span className="font-semibold text-slate-900 dark:text-white">{exp.role || "Engineer"}</span>
                          {exp.company && <span> at {exp.company}</span>}
                          {exp.duration && <span className="text-slate-400"> ({exp.duration})</span>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400">No experience timeline stated.</p>
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 mb-2">
                    <GraduationCap className="h-4 w-4 text-brand-500" />
                    <span>Education</span>
                  </div>
                  {candidate.profile.education && candidate.profile.education.length > 0 ? (
                    <div className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                      {candidate.profile.education.map((edu, idx) => (
                        <div key={idx}>
                          {edu.degree} {edu.field_of_study && `- ${edu.field_of_study}`}
                          {edu.institution && <span className="text-slate-400"> ({edu.institution})</span>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400">No education entries extracted.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Generated Questions Preview Notice */}
            <div className="mt-8 rounded-xl bg-slate-50 dark:bg-slate-800/60 p-4 border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Sparkles className="h-5 w-5 text-brand-500" />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                  {questions.length} questions tailored directly to your projects and skills.
                </span>
              </div>

              <button
                onClick={handleStartInterview}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-bold text-white shadow-md shadow-brand-500/25 transition hover:bg-brand-700 focus-visible:outline focus-visible:outline-2 active:scale-95"
              >
                <span>Start Interview</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Upload Card (Step 2) */
        <div className="space-y-8">
          <div className="text-center max-w-xl mx-auto">
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Upload Your Resume
            </h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              Upload your PDF resume. Our system will extract your background and generate a personalized mock interview.
            </p>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900 max-w-2xl mx-auto">
            {/* Drag & Drop Zone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-colors ${
                isDragging
                  ? "border-brand-500 bg-brand-50/50 dark:border-brand-400 dark:bg-brand-950/20"
                  : "border-slate-300 hover:border-brand-400 hover:bg-slate-50/50 dark:border-slate-700 dark:hover:border-slate-600 dark:hover:bg-slate-800/40"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileSelection(e.target.files[0]);
                  }
                }}
              />

              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-950/50 dark:text-brand-400 mb-4 shadow-sm">
                <UploadCloud className="h-8 w-8" />
              </div>

              <div className="text-base font-semibold text-slate-800 dark:text-slate-200">
                {selectedFile ? selectedFile.name : "Click to browse or drag and drop your resume"}
              </div>

              <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
                Supports PDF format only (maximum file size 10 MB)
              </p>

              {selectedFile && (
                <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-slate-100 dark:bg-slate-800 px-3.5 py-1 text-xs font-medium text-slate-700 dark:text-slate-300">
                  <FileText className="h-3.5 w-3.5 text-brand-500" />
                  <span>{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</span>
                </div>
              )}
            </div>

            {/* Error Message */}
            {errorMsg && (
              <div className="mt-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
                <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Upload & Process Button */}
            <div className="mt-6 flex flex-col gap-3">
              <button
                disabled={!selectedFile || isProcessing}
                onClick={handleUploadAndProcess}
                className="inline-flex w-full items-center justify-center gap-2.5 rounded-xl bg-brand-600 py-3.5 text-sm font-semibold text-white shadow-md shadow-brand-500/20 transition-all hover:bg-brand-700 focus-visible:outline focus-visible:outline-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>{processingStage}</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Analyze Resume & Generate Questions</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

