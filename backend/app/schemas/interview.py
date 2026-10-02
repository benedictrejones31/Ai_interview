from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.candidate import CandidateResponse
from app.schemas.question import QuestionResponse
from app.schemas.report import FinalInterviewReport


class InterviewCreate(BaseModel):
    candidate_id: str
    total_questions: int = 12


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_questions: int
    completed_questions: int
    overall_score: Optional[float] = None
    created_at: datetime


class InterviewStartResponse(BaseModel):
    interview_id: str
    candidate_name: str
    status: str
    welcome_message: str
    first_question: QuestionResponse


class InterviewDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    candidate: CandidateResponse
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_questions: int
    completed_questions: int
    overall_score: Optional[float] = None
    questions: List[QuestionResponse] = []
    final_report: Optional[FinalInterviewReport] = None
    created_at: datetime

