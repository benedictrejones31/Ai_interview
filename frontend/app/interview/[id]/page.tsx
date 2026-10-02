"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Mic,
  MicOff,
  Volume2,
  Brain,
  AlertCircle,
  Loader2,
  Sparkles,
  Send,
  Flag,
  CheckCircle2,
  ChevronRight,
  HelpCircle,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { RealtimeVoiceSession } from "@/lib/realtime";
import { InterviewDetail, Question } from "@/types";
import VoiceVisualizer from "@/components/VoiceVisualizer";

export default function InterviewRoomPage() {
  const router = useRouter();
  const params = useParams();
  const interviewId = params?.id as string;

  // Interview state
  const [interview, setInterview] = useState<InterviewDetail | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [currentIndex, setCurrentIndex] = useState<number>(1);
  const [totalQuestions, setTotalQuestions] = useState<number>(12);
  const [isStarted, setIsStarted] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Status: "idle" | "connecting" | "speaking" | "listening" | "thinking" | "completed" | "error"
  const [agentStatus, setAgentStatus] = useState<"idle" | "connecting" | "speaking" | "listening" | "thinking" | "completed" | "error">("idle");

  // Voice & Transcript state
  const [aiTranscript, setAiTranscript] = useState<string>("");
  const [candidateTranscript, setCandidateTranscript] = useState<string>("");
  const [evaluationFeedback, setEvaluationFeedback] = useState<string | null>(null);

  // Realtime & Speech Recognition references
  const realtimeSessionRef = useRef<RealtimeVoiceSession | null>(null);
  const webSpeechRecognitionRef = useRef<any>(null);
  const startTimeRef = useRef<number>(Date.now());

  // Load Interview Info on Mount
  useEffect(() => {
    async function loadInterviewData() {
      try {
        setIsLoading(true);
        const data = await api.getInterview(interviewId);
        setInterview(data);
        setTotalQuestions(data.total_questions || 12);

        // Find current uncompleted question
        if (data.questions && data.questions.length > 0) {
          const firstUnanswered = data.questions[data.completed_questions || 0] || data.questions[0];
          setCurrentQuestion(firstUnanswered);
          setCurrentIndex(firstUnanswered.question_order);
        }
      } catch (err: any) {
        setErrorMsg("Failed to load interview details. " + (err.message || ""));
      } finally {
        setIsLoading(false);
      }
    }

    if (interviewId) {
      loadInterviewData();
    }

    return () => {
      // Cleanup WebRTC and mic on unmount
      if (realtimeSessionRef.current) {
        realtimeSessionRef.current.stop();
      }
      if (webSpeechRecognitionRef.current) {
        webSpeechRecognitionRef.current.stop();
      }
    };
  }, [interviewId]);

  // Setup Browser Speech Recognition Fallback (for systems without WebRTC Realtime or text fallback)
  const initWebSpeechRecognition = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event: any) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        setCandidateTranscript(transcript);
        setAgentStatus("listening");
      };

      recognition.onerror = (event: any) => {
        console.warn("Speech recognition notice:", event.error);
      };

      webSpeechRecognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn("Could not start Web Speech Recognition:", err);
    }
  };

  // Browser Text-To-Speech Fallback (if OpenAI Realtime WebRTC is blocked/fails)
  const speakWithBrowserTTS = (text: string, onEnd?: () => void) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      onEnd?.();
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.onstart = () => {
      setAgentStatus("speaking");
      setAiTranscript(text);
    };
    utterance.onend = () => {
      setAgentStatus("listening");
      onEnd?.();
    };
    window.speechSynthesis.speak(utterance);
  };

  // 1. Explicit Candidate Click to Start Interview (Section 12)
  const handleStartInterview = async () => {
    setErrorMsg(null);
    setAgentStatus("connecting");
    setIsStarted(true);

    try {
      // 1. Call backend start
      const startRes = await api.startInterview(interviewId);
      setCurrentQuestion(startRes.first_question);
      setCurrentIndex(startRes.first_question.question_order);
      setAiTranscript(startRes.welcome_message);

      // 2. Try establishing OpenAI Realtime session with backend ephemeral token
      try {
        const sessionRes = await api.createRealtimeSession(interviewId, startRes.first_question.id);
        
        const rSession = new RealtimeVoiceSession({
          onStatusChange: (status) => setAgentStatus(status),
          onAiTranscriptDelta: (delta) => setAiTranscript((prev) => prev + delta),
          onAiTranscriptComplete: (text) => setAiTranscript(text),
          onUserTranscriptComplete: (text) => {
            setCandidateTranscript((prev) => (prev ? prev + " " + text : text));
          },
          onError: (err) => {
            console.warn("OpenAI Realtime WebRTC notice (switching to hybrid audio fallback):", err);
            speakWithBrowserTTS(startRes.welcome_message + " " + startRes.first_question.question_text);
            initWebSpeechRecognition();
          }
        });

        await rSession.start(sessionRes.client_secret, sessionRes.model);
        realtimeSessionRef.current = rSession;
      } catch (realtimeErr) {
        console.warn("Realtime WebRTC initialization bypassed or unavailable. Using audio speech fallback:", realtimeErr);
        // Fallback to high-quality browser speech synthesis + recognition
        speakWithBrowserTTS(startRes.welcome_message + " " + startRes.first_question.question_text);
        initWebSpeechRecognition();
      }

      startTimeRef.current = Date.now();
    } catch (err: any) {
      setAgentStatus("error");
      setErrorMsg(err.message || "Could not start interview session.");
    }
  };

  // 2. Submit candidate's answer for evaluation & progress
  const handleSubmitAnswer = async () => {
    if (!currentQuestion || !candidateTranscript.trim() || isEvaluating) return;

    setIsEvaluating(true);
    setAgentStatus("thinking");
    const durationSeconds = (Date.now() - startTimeRef.current) / 1000;

    try {
      const response = await api.submitAnswer(
        interviewId,
        currentQuestion.id,
        candidateTranscript.trim(),
        durationSeconds
      );

      // Show brief feedback badge
      setEvaluationFeedback(response.evaluation.feedback);
      setTotalQuestions(response.total_questions);

      // Check if interview completed
      if (response.is_interview_completed || !response.next_question) {
        setAgentStatus("completed");
        const completionMsg =
          "Thank you for completing the interview. That concludes our session. Your responses will now be evaluated and your interview report will be prepared.";
        setAiTranscript(completionMsg);

        if (realtimeSessionRef.current?.active) {
          realtimeSessionRef.current.sendTextMessage(
            "Say aloud: 'Thank you for completing the interview. That concludes our session. Your responses will now be evaluated and your interview report will be prepared.'"
          );
        } else {
          speakWithBrowserTTS(completionMsg);
        }

        setTimeout(() => {
          handleCompleteInterview();
        }, 4000);
        return;
      }

      // Check for follow-up or next question
      const nextQ = response.follow_up_question || response.next_question;
      if (nextQ) {
        setCurrentQuestion(nextQ);
        setCurrentIndex(nextQ.question_order);
        setCandidateTranscript("");
        startTimeRef.current = Date.now();

        // Speak the next question
        const promptToSpeak = nextQ.question_text;
        setAiTranscript(promptToSpeak);

        if (realtimeSessionRef.current?.active) {
          realtimeSessionRef.current.sendTextMessage(`Ask this question clearly to the candidate: "${promptToSpeak}"`);
        } else {
          speakWithBrowserTTS(promptToSpeak);
        }
      }
    } catch (err: any) {
      setErrorMsg("Failed to evaluate answer: " + (err.message || "Unknown error"));
      setAgentStatus("listening");
    } finally {
      setIsEvaluating(false);
    }
  };

  // 3. Finalize interview & generate full report
  const handleCompleteInterview = async () => {
    try {
      setAgentStatus("thinking");
      setIsLoading(true);
      if (realtimeSessionRef.current) {
        realtimeSessionRef.current.stop();
      }
      await api.completeInterview(interviewId);
      router.push(`/report/${interviewId}`);
    } catch (err: any) {
      setErrorMsg("Error finalizing report: " + (err.message || ""));
      setIsLoading(false);
    }
  };

  if (isLoading && !interview) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-brand-600 mb-4" />
        <p className="text-slate-600 dark:text-slate-300 font-medium">Preparing interview chamber...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between pb-6 border-b border-slate-200 dark:border-slate-800 gap-4">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            AI Voice Interview
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
            {interview?.candidate?.name ? `${interview.candidate.name}'s Technical Session` : "Technical Session"}
          </h1>
        </div>

        {/* Question Counter Progress */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs font-semibold text-slate-500 dark:text-slate-400">Progress</div>
            <div className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Question {currentIndex} of {totalQuestions}
            </div>
          </div>
          <div className="w-28 h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
            <div
              className="h-full bg-brand-600 transition-all duration-500 ease-out"
              style={{ width: `${Math.min(100, (currentIndex / totalQuestions) * 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Error alert */}
      {errorMsg && (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Pre-Interview Start Card (Section 12) */}
      {!isStarted ? (
        <div className="mt-12 rounded-3xl border border-slate-200 bg-white p-8 sm:p-12 shadow-sm dark:border-slate-800 dark:bg-slate-900 text-center max-w-2xl mx-auto">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400 mb-6 shadow-sm">
            <Mic className="h-10 w-10" />
          </div>

          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            Ready to Begin Your Voice Interview?
          </h2>

          <p className="mt-4 text-sm text-slate-600 dark:text-slate-300 leading-relaxed max-w-lg mx-auto">
            The AI interviewer will speak instructions and questions out loud. Make sure your microphone is connected and you are in a quiet environment.
          </p>

          <div className="mt-6 inline-flex flex-col text-left gap-2 bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl text-xs text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span>Listen carefully to each question spoken by the AI</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span>Speak clearly into your microphone when answering</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span>Take a few seconds to think before answering</span>
            </div>
          </div>

          <div className="mt-8">
            <button
              onClick={handleStartInterview}
              className="inline-flex items-center gap-2.5 rounded-2xl bg-brand-600 px-8 py-4 text-base font-bold text-white shadow-lg shadow-brand-500/25 transition-all hover:bg-brand-700 hover:shadow-brand-500/35 focus-visible:outline focus-visible:outline-2 active:scale-95"
            >
              <Mic className="h-5 w-5" />
              <span>Start Interview</span>
            </button>
          </div>
        </div>
      ) : (
        /* Live Interview Chamber (Section 14) */
        <div className="mt-8 space-y-6 animate-fadeIn">
          {/* Status Indicator Bar */}
          <div className="flex items-center justify-between rounded-xl bg-white dark:bg-slate-900 px-5 py-3 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="relative flex h-3 w-3">
                <span
                  className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    agentStatus === "speaking"
                      ? "animate-ping bg-brand-400"
                      : agentStatus === "listening"
                      ? "animate-ping bg-emerald-400"
                      : agentStatus === "thinking"
                      ? "animate-ping bg-amber-400"
                      : "bg-slate-400"
                  }`}
                />
                <span
                  className={`relative inline-flex h-3 w-3 rounded-full ${
                    agentStatus === "speaking"
                      ? "bg-brand-600"
                      : agentStatus === "listening"
                      ? "bg-emerald-600"
                      : agentStatus === "thinking"
                      ? "bg-amber-600"
                      : "bg-slate-500"
                  }`}
                />
              </span>
              <span className="text-sm font-semibold capitalize text-slate-800 dark:text-slate-200">
                {agentStatus === "speaking"
                  ? "AI Speaking..."
                  : agentStatus === "listening"
                  ? "Listening to your answer..."
                  : agentStatus === "thinking"
                  ? "Evaluating & Thinking..."
                  : agentStatus === "connecting"
                  ? "Connecting session..."
                  : "Interview Ready"}
              </span>
            </div>

            {/* Audio Wave Visualizer */}
            <VoiceVisualizer status={agentStatus} mode={agentStatus === "speaking" ? "ai" : "user"} />
          </div>

          {/* AI Interviewer Speech Box */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 transition-all">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
              <div className="flex items-center gap-2 text-sm font-bold text-brand-600 dark:text-brand-400">
                <Volume2 className="h-4 w-4" />
                <span>AI Interviewer</span>
                {currentQuestion?.category && (
                  <span className="ml-2 rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wider text-slate-600 dark:text-slate-300">
                    {currentQuestion.category.replace("_", " ")}
                  </span>
                )}
                {currentQuestion?.is_follow_up && (
                  <span className="rounded-md bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 px-2 py-0.5 text-[11px] font-medium text-amber-700 dark:text-amber-400">
                    Follow-Up
                  </span>
                )}
              </div>

              {agentStatus === "speaking" && (
                <span className="text-xs font-semibold text-brand-600 animate-pulse">● Speaking</span>
              )}
            </div>

            <div className="mt-4">
              <p className="text-lg sm:text-xl font-medium text-slate-800 dark:text-slate-100 leading-relaxed">
                "{currentQuestion?.question_text || aiTranscript}"
              </p>
            </div>
          </div>

          {/* Candidate Microphone & Answer Box */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
              <div className="flex items-center gap-2 text-sm font-bold text-emerald-600 dark:text-emerald-400">
                <Mic className="h-4 w-4" />
                <span>Candidate Response</span>
              </div>

              <div className="flex items-center gap-2">
                {agentStatus === "listening" && (
                  <span className="text-xs font-semibold text-emerald-600 animate-pulse">● Microphone Active</span>
                )}
              </div>
            </div>

            {/* Spoken Transcript Area */}
            <div className="mt-4 min-h-[100px] rounded-xl bg-slate-50 dark:bg-slate-800/40 p-4 border border-slate-200/80 dark:border-slate-700">
              {candidateTranscript ? (
                <p className="text-base text-slate-800 dark:text-slate-200 leading-relaxed">
                  {candidateTranscript}
                </p>
              ) : (
                <p className="text-sm italic text-slate-400">
                  Your spoken answer will appear here as you speak into the microphone...
                </p>
              )}
            </div>

            {/* Answer editing fallback textarea if user wants to make adjustments */}
            <div className="mt-3">
              <textarea
                value={candidateTranscript}
                onChange={(e) => setCandidateTranscript(e.target.value)}
                placeholder="Or type/edit your answer here..."
                rows={2}
                className="w-full text-xs text-slate-600 dark:text-slate-300 bg-transparent rounded-lg border border-slate-200 dark:border-slate-700 p-2.5 focus:border-brand-500 focus:outline-none resize-none"
              />
            </div>

            {/* Feedback alert from previous question if any */}
            {evaluationFeedback && (
              <div className="mt-3 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 p-3 text-xs text-blue-700 dark:text-blue-300 flex items-start gap-2">
                <Sparkles className="h-4 w-4 shrink-0 text-blue-500" />
                <span>AI Evaluator Note: {evaluationFeedback}</span>
              </div>
            )}

            {/* Controls Bar */}
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={handleCompleteInterview}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 dark:border-slate-700 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                <Flag className="h-3.5 w-3.5" />
                <span>End Interview</span>
              </button>

              <button
                disabled={!candidateTranscript.trim() || isEvaluating}
                onClick={handleSubmitAnswer}
                className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-2.5 text-sm font-bold text-white shadow-md shadow-brand-500/20 hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isEvaluating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Evaluating Response...</span>
                  </>
                ) : (
                  <>
                    <span>Submit & Continue</span>
                    <ChevronRight className="h-4 w-4" />
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

