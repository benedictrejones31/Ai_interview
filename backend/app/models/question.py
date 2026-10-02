import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    question_order = Column(Integer, nullable=False, index=True)
    category = Column(String(100), nullable=False)  # introduction, resume, technical_skills, projects, experience, problem_solving, behavioral
    question_text = Column(Text, nullable=False)
    skills_tested_json = Column(JSON, nullable=False, default=list)
    difficulty = Column(String(50), default="intermediate", nullable=False)  # basic, intermediate, advanced
    expected_topics_json = Column(JSON, nullable=False, default=list)
    is_follow_up = Column(Boolean, default=False, nullable=False)
    parent_question_id = Column(String(36), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    interview = relationship("Interview", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    follow_ups = relationship("Question", backref="parent_question", remote_side=[id])

