"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Mic,
  MicOff,
  Volume2,
  Sparkles,
  AlertCircle,
  Loader2,
  Flag,
  CheckCircle2,
  ChevronRight,
  RotateCcw,
  Radio,
} from "lucide-react";
import { api } from "@/lib/api";
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
  const [agentStatus, setAgentStatus] = useState<
    "idle" | "connecting" | "speaking" | "listening" | "thinking" | "completed" | "error"
  >("idle");

  // Voice & Transcript state
  const [aiTranscript, setAiTranscript] = useState<string>("");
  const [candidateTranscript, setCandidateTranscript] = useState<string>("");
  const [evaluationFeedback, setEvaluationFeedback] = useState<string | null>(null);

  // Auto-submit silence countdown state
  const [silenceCountdown, setSilenceCountdown] = useState<number | null>(null);

  // Refs for audio lifecycle
  const recognitionRef = useRef<any>(null);
  const isSpeakingRef = useRef<boolean>(false);
  const isEvaluatingRef = useRef<boolean>(false);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const accumulatedFinalTextRef = useRef<string>("");
  const currentTranscriptRef = useRef<string>("");
  const startTimeRef = useRef<number>(Date.now());
  const activeQuestionRef = useRef<Question | null>(null);

  // Keep activeQuestionRef in sync
  useEffect(() => {
    activeQuestionRef.current = currentQuestion;
  }, [currentQuestion]);

  // Keep currentTranscriptRef in sync
  useEffect(() => {
    currentTranscriptRef.current = candidateTranscript;
  }, [candidateTranscript]);

  // Clear silence detection timers
  const clearSilenceTimers = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
      countdownIntervalRef.current = null;
    }
    setSilenceCountdown(null);
  }, []);

  // Stop microphone recognition safely
  const stopListening = useCallback(() => {
    clearSilenceTimers();
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.stop();
      } catch (e) {
        // Ignore errors when stopping
      }
      recognitionRef.current = null;
    }
  }, [clearSilenceTimers]);

  // Forward declaration for handleSubmitAnswer
  const handleSubmitAnswerRef = useRef<(textToSubmit?: string) => Promise<void>>();

  // Start Voice Recognition (STT)
  const startListening = useCallback(() => {
    if (typeof window === "undefined") return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setErrorMsg(
        "Speech recognition is not supported in this browser. Please use Google Chrome, Microsoft Edge, or Safari."
      );
      return;
    }

    // Stop any existing instance
    stopListening();

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setAgentStatus("listening");
      };

      recognition.onresult = (event: any) => {
        // If AI is speaking or system is evaluating, discard accidental input
        if (isSpeakingRef.current || isEvaluatingRef.current) return;

        let interimText = "";
        let newFinalText = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const result = event.results[i];
          if (result.isFinal) {
            newFinalText += result[0].transcript + " ";
          } else {
            interimText += result[0].transcript;
          }
        }

        if (newFinalText) {
          accumulatedFinalTextRef.current = (
            accumulatedFinalTextRef.current + " " + newFinalText
          )
            .replace(/\s+/g, " ")
            .trim();
        }

        const fullAnswer = (accumulatedFinalTextRef.current + " " + interimText)
          .replace(/\s+/g, " ")
          .trim();

        setCandidateTranscript(fullAnswer);
        currentTranscriptRef.current = fullAnswer;

        // Reset silence detection
        clearSilenceTimers();

        // 1. Check for verbal finish command: "I'm done", "that's my answer", "next question"
        const lower = fullAnswer.toLowerCase();
        const hasVoiceCompletion =
          lower.endsWith("i'm done") ||
          lower.endsWith("i am done") ||
          lower.endsWith("that's my answer") ||
          lower.endsWith("that is my answer") ||
          lower.endsWith("next question") ||
          lower.endsWith("done answering");

        if (hasVoiceCompletion && fullAnswer.length >= 15) {
          if (handleSubmitAnswerRef.current) {
            handleSubmitAnswerRef.current(fullAnswer);
          }
          return;
        }

        // 2. Natural Silence Detection / Auto-Advance (Hands-Free Voice Flow)
        // If candidate has spoken at least 4 words or 15 chars, start auto-advance countdown
        const wordCount = fullAnswer.split(" ").filter(Boolean).length;
        if (wordCount >= 4) {
          let count = 3;
          setSilenceCountdown(count);

          countdownIntervalRef.current = setInterval(() => {
            count -= 1;
            if (count > 0) {
              setSilenceCountdown(count);
            } else {
              setSilenceCountdown(null);
            }
          }, 1000);

          silenceTimerRef.current = setTimeout(() => {
            clearSilenceTimers();
            // Auto submit answer via voice
            if (handleSubmitAnswerRef.current && currentTranscriptRef.current.trim().length >= 10) {
              handleSubmitAnswerRef.current(currentTranscriptRef.current);
            }
          }, 3000);
        }
      };

      recognition.onerror = (event: any) => {
        // 'no-speech' is normal when user is thinking before answering
        if (event.error === "no-speech") return;
        if (event.error === "not-allowed") {
          setErrorMsg("Microphone access was denied. Please allow microphone permissions in your browser.");
        }
      };

      recognition.onend = () => {
        // If we are still in listening mode and not speaking or evaluating, restart continuous recognition
        if (!isSpeakingRef.current && !isEvaluatingRef.current) {
          try {
            recognition.start();
          } catch (e) {
            // Ignore if already active
          }
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      console.warn("Speech recognition failed to start:", err);
    }
  }, [stopListening, clearSilenceTimers]);

  // Speak AI response through Browser SpeechSynthesis (TTS)
  const speakAIResponse = useCallback(
    (textToSpeak: string, onFinish?: () => void) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) {
        onFinish?.();
        return;
      }

      // Mark speaking state and stop mic so it doesn't transcribe itself
      isSpeakingRef.current = true;
      stopListening();
      clearSilenceTimers();
      setAgentStatus("speaking");
      setAiTranscript(textToSpeak);

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.rate = 0.98;
      utterance.pitch = 1.0;

      // Select a natural sounding English voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice =
        voices.find(
          (v) =>
            v.lang.startsWith("en") &&
            (v.name.includes("Natural") ||
              v.name.includes("Google") ||
              v.name.includes("Samantha") ||
              v.name.includes("David") ||
              v.name.includes("Microsoft") ||
              v.name.includes("English"))
        ) || voices.find((v) => v.lang.startsWith("en"));

      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      utterance.onstart = () => {
        isSpeakingRef.current = true;
        setAgentStatus("speaking");
      };

      utterance.onend = () => {
        isSpeakingRef.current = false;
        setAgentStatus("listening");
        // AI finished speaking: activate microphone for candidate's voice answer
        accumulatedFinalTextRef.current = "";
        setCandidateTranscript("");
        currentTranscriptRef.current = "";
        startListening();
        onFinish?.();
      };

      utterance.onerror = (err) => {
        console.warn("Speech synthesis notice:", err);
        isSpeakingRef.current = false;
        setAgentStatus("listening");
        accumulatedFinalTextRef.current = "";
        setCandidateTranscript("");
        currentTranscriptRef.current = "";
        startListening();
        onFinish?.();
      };

      window.speechSynthesis.speak(utterance);
    },
    [stopListening, clearSilenceTimers, startListening]
  );

  // Submit Answer to Backend (Google Gemini Scoring & Follow-up decision)
  const handleSubmitAnswer = async (textToSubmit?: string) => {
    const answer = (textToSubmit || currentTranscriptRef.current || candidateTranscript).trim();
    const q = activeQuestionRef.current || currentQuestion;

    if (!q || !answer || isEvaluatingRef.current) return;

    isEvaluatingRef.current = true;
    setIsEvaluating(true);
    clearSilenceTimers();
    stopListening();
    setAgentStatus("thinking");

    const durationSeconds = Math.max(3, Math.round((Date.now() - startTimeRef.current) / 1000));

    try {
      const response = await api.submitAnswer(
        interviewId,
        q.id,
        answer,
        durationSeconds
      );

      setEvaluationFeedback(response.evaluation.feedback);
      setTotalQuestions(response.total_questions);

      // Check if interview completed
      if (response.is_interview_completed || !response.next_question) {
        setAgentStatus("completed");
        const completionMsg =
          "Thank you for completing your interview. That concludes all questions. I am now compiling your comprehensive performance report.";
        setAiTranscript(completionMsg);

        speakAIResponse(completionMsg, () => {
          handleCompleteInterview();
        });
        return;
      }

      // Progress to follow-up or next question
      const nextQ = response.follow_up_question || response.next_question;
      if (nextQ) {
        setCurrentQuestion(nextQ);
        activeQuestionRef.current = nextQ;
        setCurrentIndex(nextQ.question_order);
        setCandidateTranscript("");
        accumulatedFinalTextRef.current = "";
        currentTranscriptRef.current = "";
        startTimeRef.current = Date.now();

        // Speak the new question out loud through voice
        speakAIResponse(nextQ.question_text);
      }
    } catch (err: any) {
      setErrorMsg("Failed to evaluate answer: " + (err.message || "Unknown error"));
      setAgentStatus("listening");
      startListening();
    } finally {
      isEvaluatingRef.current = false;
      setIsEvaluating(false);
    }
  };

  // Assign ref for callback usage
  handleSubmitAnswerRef.current = handleSubmitAnswer;

  // Repeat current question aloud
  const handleRepeatQuestion = () => {
    if (!currentQuestion) return;
    speakAIResponse("I will repeat the question: " + currentQuestion.question_text);
  };

  // Complete Interview & Route to Report
  const handleCompleteInterview = async () => {
    try {
      setAgentStatus("thinking");
      setIsLoading(true);
      stopListening();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      await api.completeInterview(interviewId);
      router.push(`/report/${interviewId}`);
    } catch (err: any) {
      setErrorMsg("Error finalizing report: " + (err.message || ""));
      setIsLoading(false);
    }
  };

  // Load Interview Info on Mount
  useEffect(() => {
    async function loadInterviewData() {
      try {
        setIsLoading(true);
        const data = await api.getInterview(interviewId);
        setInterview(data);
        setTotalQuestions(data.total_questions || 12);

        if (data.questions && data.questions.length > 0) {
          const firstUnanswered =
            data.questions[data.completed_questions || 0] || data.questions[0];
          setCurrentQuestion(firstUnanswered);
          activeQuestionRef.current = firstUnanswered;
          setCurrentIndex(firstUnanswered.question_order);
        }
      } catch (err: any) {
        setErrorMsg("Failed to load interview details: " + (err.message || ""));
      } finally {
        setIsLoading(false);
      }
    }

    if (interviewId) {
      loadInterviewData();
    }

    // Load available speech voices
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }

    return () => {
      stopListening();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [interviewId, stopListening]);

  // Start Interview Flow
  const handleStartInterview = async () => {
    setErrorMsg(null);
    setAgentStatus("connecting");
    setIsStarted(true);

    try {
      const startRes = await api.startInterview(interviewId);
      const firstQ = startRes.first_question;
      setCurrentQuestion(firstQ);
      activeQuestionRef.current = firstQ;
      setCurrentIndex(firstQ.question_order);

      const promptToSpeak = `${startRes.welcome_message} ${firstQ.question_text}`;
      startTimeRef.current = Date.now();

      // AI speaks the introduction and first question aloud
      speakAIResponse(promptToSpeak);
    } catch (err: any) {
      setAgentStatus("error");
      setErrorMsg(err.message || "Could not start interview session.");
    }
  };

  if (isLoading && !interview) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-brand-600 mb-4" />
        <p className="text-slate-600 dark:text-slate-300 font-medium">
          Preparing your AI voice interview chamber...
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between pb-6 border-b border-slate-200 dark:border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
              AI Voice Interview
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              <Radio className="h-3 w-3 animate-pulse text-emerald-500" />
              100% Voice-Driven
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
            {interview?.candidate?.name
              ? `${interview.candidate.name}'s Technical Interview`
              : "Technical Interview"}
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
              style={{
                width: `${Math.min(100, (currentIndex / totalQuestions) * 100)}%`,
              }}
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

      {/* Pre-Interview Start Card */}
      {!isStarted ? (
        <div className="mt-12 rounded-3xl border border-slate-200 bg-white p-8 sm:p-12 shadow-sm dark:border-slate-800 dark:bg-slate-900 text-center max-w-2xl mx-auto">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-brand-50 text-brand-600 dark:bg-brand-950/60 dark:text-brand-400 mb-6 shadow-sm">
            <Mic className="h-10 w-10 animate-pulse" />
          </div>

          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            Ready to Begin Your AI Voice Interview?
          </h2>

          <p className="mt-4 text-sm text-slate-600 dark:text-slate-300 leading-relaxed max-w-lg mx-auto">
            The AI interviewer will ask questions out loud through voice. When the question finishes, speak your answer naturally into your microphone.
          </p>

          <div className="mt-6 inline-flex flex-col text-left gap-2.5 bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl text-xs text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span><strong>Hands-Free Auto-Advance:</strong> When you finish speaking and pause, your answer is automatically submitted.</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span><strong>Listen First:</strong> The microphone turns on automatically as soon as the AI finishes speaking.</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              <span><strong>Spoken Commands:</strong> You can say <em>&quot;I am done&quot;</em> or <em>&quot;Next question&quot;</em> to proceed immediately.</span>
            </div>
          </div>

          <div className="mt-8">
            <button
              onClick={handleStartInterview}
              className="inline-flex items-center gap-2.5 rounded-2xl bg-brand-600 px-8 py-4 text-base font-bold text-white shadow-lg shadow-brand-500/25 transition-all hover:bg-brand-700 hover:shadow-brand-500/35 focus-visible:outline focus-visible:outline-2 active:scale-95 cursor-pointer"
            >
              <Mic className="h-5 w-5" />
              <span>Start Voice Interview</span>
            </button>
          </div>
        </div>
      ) : (
        /* Live Voice Chamber */
        <div className="mt-8 space-y-6 animate-fadeIn">
          {/* Status Bar */}
          <div className="flex items-center justify-between rounded-xl bg-white dark:bg-slate-900 px-5 py-3 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="relative flex h-3.5 w-3.5">
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
                  className={`relative inline-flex h-3.5 w-3.5 rounded-full ${
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
                  ? "AI Speaking Question..."
                  : agentStatus === "listening"
                  ? "Listening To Your Answer (Speak into microphone)..."
                  : agentStatus === "thinking"
                  ? "AI Evaluating Answer & Preparing Next Question..."
                  : agentStatus === "connecting"
                  ? "Connecting voice session..."
                  : "Interview Ready"}
              </span>
            </div>

            {/* Audio Wave Visualizer */}
            <VoiceVisualizer
              status={agentStatus}
              mode={agentStatus === "speaking" ? "ai" : "user"}
            />
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
                    Adaptive Follow-Up
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {agentStatus === "speaking" ? (
                  <span className="text-xs font-semibold text-brand-600 animate-pulse">
                    ● Speaking Aloud
                  </span>
                ) : (
                  <button
                    onClick={handleRepeatQuestion}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-brand-600 transition dark:text-slate-400"
                    title="Repeat Question"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    <span>Repeat Question</span>
                  </button>
                )}
              </div>
            </div>

            <div className="mt-4">
              <p className="text-lg sm:text-xl font-medium text-slate-800 dark:text-slate-100 leading-relaxed">
                &ldquo;{currentQuestion?.question_text || aiTranscript}&rdquo;
              </p>
            </div>
          </div>

          {/* Candidate Response & Live Voice Box */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
              <div className="flex items-center gap-2 text-sm font-bold text-emerald-600 dark:text-emerald-400">
                <Mic className="h-4 w-4" />
                <span>Candidate Voice Response</span>
              </div>

              <div className="flex items-center gap-3">
                {/* Silence Countdown Indicator */}
                {silenceCountdown !== null && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-700 px-3 py-1 text-xs font-bold text-amber-700 dark:text-amber-300 animate-pulse">
                    <span>Moving to next question in {silenceCountdown}s...</span>
                  </span>
                )}

                {agentStatus === "listening" && (
                  <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                    <span>Microphone Active</span>
                  </span>
                )}
              </div>
            </div>

            {/* Live Spoken Transcript Area */}
            <div className="mt-4 min-h-[110px] rounded-xl bg-slate-50 dark:bg-slate-800/40 p-4 border border-slate-200/80 dark:border-slate-700 transition-all">
              {candidateTranscript ? (
                <p className="text-base text-slate-800 dark:text-slate-100 leading-relaxed font-normal">
                  {candidateTranscript}
                </p>
              ) : agentStatus === "listening" ? (
                <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 italic">
                  <Mic className="h-4 w-4 animate-pulse text-emerald-500" />
                  <span>Listening... Speak your answer now. When you finish, the interview advances automatically.</span>
                </div>
              ) : agentStatus === "speaking" ? (
                <p className="text-sm italic text-slate-400 dark:text-slate-500">
                  Please listen to the AI interviewer. Your microphone will turn on as soon as the question finishes.
                </p>
              ) : (
                <p className="text-sm italic text-slate-400">
                  Processing evaluation...
                </p>
              )}
            </div>

            {/* Text adjustment backup (optional) */}
            <div className="mt-3">
              <textarea
                value={candidateTranscript}
                onChange={(e) => {
                  setCandidateTranscript(e.target.value);
                  currentTranscriptRef.current = e.target.value;
                }}
                placeholder="Spoken words transcribe here automatically. You can also edit if needed..."
                rows={2}
                className="w-full text-xs text-slate-600 dark:text-slate-300 bg-transparent rounded-lg border border-slate-200 dark:border-slate-700 p-2.5 focus:border-brand-500 focus:outline-none resize-none"
              />
            </div>

            {/* Feedback alert from previous question if any */}
            {evaluationFeedback && (
              <div className="mt-3 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 p-3 text-xs text-blue-700 dark:text-blue-300 flex items-start gap-2">
                <Sparkles className="h-4 w-4 shrink-0 text-blue-500 mt-0.5" />
                <span><strong>AI Feedback:</strong> {evaluationFeedback}</span>
              </div>
            )}

            {/* Hands-Free Notice & Controls */}
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <span>Hands-free voice mode active: pause speaking for 3s to auto-advance</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleCompleteInterview}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 dark:border-slate-700 px-3.5 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
                >
                  <Flag className="h-3.5 w-3.5" />
                  <span>End Interview</span>
                </button>

                <button
                  disabled={!candidateTranscript.trim() || isEvaluating}
                  onClick={() => handleSubmitAnswer()}
                  className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2 text-sm font-bold text-white shadow-md shadow-brand-500/20 hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {isEvaluating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Evaluating...</span>
                    </>
                  ) : (
                    <>
                      <span>Next Question</span>
                      <ChevronRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
