export interface EducationItem {
  institution?: string;
  degree?: string;
  field_of_study?: string;
  year?: string;
}

export interface ProjectItem {
  title: string;
  description?: string;
  technologies?: string[];
}

export interface ExperienceItem {
  company?: string;
  role?: string;
  duration?: string;
  highlights?: string[];
}

export interface CandidateProfile {
  name: string;
  summary: string;
  skills: string[];
  education: EducationItem[];
  projects: ProjectItem[];
  experience: ExperienceItem[];
  certifications: string[];
  target_roles: string[];
}

export interface Candidate {
  id: string;
  name: string;
  email?: string | null;
  resume_filename: string;
  profile: CandidateProfile;
  created_at: string;
}

export interface Question {
  id: string;
  interview_id: string;
  question_order: number;
  category: string;
  question_text: string;
  skills_tested: string[];
  difficulty: string;
  expected_topics: string[];
  is_follow_up: boolean;
  parent_question_id?: string | null;
  created_at: string;
}

export interface AnswerEvaluation {
  score: number;
  correctness: number;
  relevance: number;
  technical_depth: number;
  clarity: number;
  strengths: string[];
  missing_points: string[];
  feedback: string;
  needs_follow_up: boolean;
  suggested_follow_up_question?: string | null;
}

export interface AnswerSubmitResponse {
  answer_id: string;
  evaluation: AnswerEvaluation;
  follow_up_question?: Question | null;
  next_question?: Question | null;
  is_interview_completed: boolean;
  completed_questions: number;
  total_questions: number;
}

export interface CategoryScores {
  technical_knowledge: number;
  project_understanding: number;
  problem_solving: number;
  communication_clarity: number;
  resume_understanding: number;
}

export interface QuestionAnalysisItem {
  question: string;
  category: string;
  candidate_answer: string;
  score: number;
  strengths: string[];
  missing_points: string[];
  feedback: string;
}

export interface FinalInterviewReport {
  candidate_name: string;
  candidate_email?: string | null;
  interview_date: string;
  duration_minutes: number;
  total_questions_asked: number;
  overall_score: number;
  category_scores: CategoryScores;
  strengths: string[];
  areas_for_improvement: string[];
  question_analyses: QuestionAnalysisItem[];
  final_summary: string;
  recommendation: string;
}

export interface InterviewDetail {
  id: string;
  candidate_id: string;
  candidate: Candidate;
  status: "pending" | "in_progress" | "completed" | "abandoned";
  started_at?: string | null;
  completed_at?: string | null;
  total_questions: number;
  completed_questions: number;
  overall_score?: number | null;
  questions: Question[];
  final_report?: FinalInterviewReport | null;
  created_at: string;
}

export interface RealtimeSessionResponse {
  client_secret: string;
  session_id: string;
  model: string;
  voice: string;
  instructions: string;
}

export interface AdminInterviewSummary {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email?: string | null;
  resume_filename: string;
  status: string;
  overall_score?: number | null;
  completed_questions: number;
  total_questions: number;
  created_at: string;
  completed_at?: string | null;
}

