import {
  Candidate,
  InterviewDetail,
  Question,
  AnswerSubmitResponse,
  FinalInterviewReport,
  RealtimeSessionResponse,
  AdminInterviewSummary
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});
  
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch {
      // Ignore json parse error and keep default status text
    }
    throw new ApiError(errorDetail, response.status);
  }

  return response.json();
}

export const api = {
  // 1. Resume Upload
  async uploadResume(file: File): Promise<{
    candidate: Candidate;
    interview_id: string;
    total_questions: number;
    questions: Question[];
  }> {
    const formData = new FormData();
    formData.append("file", file);
    return request("/api/resumes/upload", {
      method: "POST",
      body: formData,
    });
  },

  // 2. Interview Details
  async getInterview(interviewId: string): Promise<InterviewDetail> {
    return request(`/api/interviews/${interviewId}`);
  },

  // 3. Start Interview
  async startInterview(interviewId: string): Promise<{
    interview_id: string;
    candidate_name: string;
    status: string;
    welcome_message: string;
    first_question: Question;
  }> {
    return request(`/api/interviews/${interviewId}/start`, {
      method: "POST",
    });
  },

  // 4. Submit Answer
  async submitAnswer(
    interviewId: string,
    questionId: string,
    transcript: string,
    durationSeconds?: number
  ): Promise<AnswerSubmitResponse> {
    return request(`/api/interviews/${interviewId}/answer`, {
      method: "POST",
      body: JSON.stringify({
        question_id: questionId,
        transcript,
        duration_seconds: durationSeconds,
      }),
    });
  },

  // 5. Complete Interview & Generate Report
  async completeInterview(interviewId: string): Promise<FinalInterviewReport> {
    return request(`/api/interviews/${interviewId}/complete`, {
      method: "POST",
    });
  },

  // 6. Get Stored Report
  async getReport(interviewId: string): Promise<FinalInterviewReport> {
    return request(`/api/interviews/${interviewId}/report`);
  },

  // 7. Get Ephemeral Realtime Session Token
  async createRealtimeSession(
    interviewId: string,
    questionId?: string
  ): Promise<RealtimeSessionResponse> {
    return request("/api/realtime/session", {
      method: "POST",
      body: JSON.stringify({
        interview_id: interviewId,
        question_id: questionId,
      }),
    });
  },

  // 8. Admin Interview List
  async getAdminInterviews(): Promise<AdminInterviewSummary[]> {
    return request("/api/admin/interviews");
  },

  // 9. Download Report PDF URL
  getReportPdfUrl(interviewId: string): string {
    return `${API_BASE_URL}/api/interviews/${interviewId}/pdf`;
  },

  // 10. Send Report Email to HR
  async sendReportEmail(interviewId: string): Promise<{ status: string; recipient: string; note?: string }> {
    return request(`/api/interviews/${interviewId}/send-email`, {
      method: "POST",
    });
  },
};

