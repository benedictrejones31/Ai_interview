from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class QuestionItem(BaseModel):
    order: int
    category: str  # introduction, resume, technical_skills, projects, experience, problem_solving, behavioral
    question: str
    skills_tested: List[str] = Field(default_factory=list)
    difficulty: str = "intermediate"  # basic, intermediate, advanced
    expected_topics: List[str] = Field(default_factory=list)


class GeneratedQuestionsResponse(BaseModel):
    questions: List[QuestionItem]


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    interview_id: str
    question_order: int
    category: str
    question_text: str
    skills_tested: List[str]
    difficulty: str
    expected_topics: List[str]
    is_follow_up: bool
    parent_question_id: Optional[str] = None
    created_at: datetime

