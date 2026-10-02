from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.question import QuestionResponse


class AnswerSubmitRequest(BaseModel):
    question_id: str
    transcript: str
    duration_seconds: Optional[float] = None


class AnswerEvaluation(BaseModel):
    score: int = Field(ge=0, le=100)
    correctness: int = Field(ge=1, le=10)
    relevance: int = Field(ge=1, le=10)
    technical_depth: int = Field(ge=1, le=10)
    clarity: int = Field(ge=1, le=10)
    strengths: List[str] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    feedback: str
    needs_follow_up: bool = False
    suggested_follow_up_question: Optional[str] = None


class AnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    interview_id: str
    transcript: str
    duration_seconds: Optional[float] = None
    evaluation: AnswerEvaluation
    created_at: datetime


class AnswerSubmitResponse(BaseModel):
    answer_id: str
    evaluation: AnswerEvaluation
    follow_up_question: Optional[QuestionResponse] = None
    next_question: Optional[QuestionResponse] = None
    is_interview_completed: bool = False
    completed_questions: int
    total_questions: int

