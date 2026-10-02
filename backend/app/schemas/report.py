from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class QuestionAnalysisItem(BaseModel):
    question: str
    category: str
    candidate_answer: str
    score: int
    strengths: List[str] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    feedback: str


class CategoryScores(BaseModel):
    technical_knowledge: int = Field(ge=0, le=100)
    project_understanding: int = Field(ge=0, le=100)
    problem_solving: int = Field(ge=0, le=100)
    communication_clarity: int = Field(ge=0, le=100)
    resume_understanding: int = Field(ge=0, le=100)


class FinalInterviewReport(BaseModel):
    candidate_name: str
    candidate_email: Optional[str] = None
    interview_date: str
    duration_minutes: float
    total_questions_asked: int
    overall_score: int = Field(ge=0, le=100)
    category_scores: CategoryScores
    strengths: List[str]
    areas_for_improvement: List[str]
    question_analyses: List[QuestionAnalysisItem]
    final_summary: str
    recommendation: str = "Human Review Recommended"

