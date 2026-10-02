import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, in_progress, completed, abandoned
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_questions = Column(Integer, default=12, nullable=False)
    completed_questions = Column(Integer, default=0, nullable=False)
    overall_score = Column(Float, nullable=True)
    final_report_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="interviews")
    questions = relationship("Question", back_populates="interview", cascade="all, delete-orphan", order_by="Question.question_order")
    answers = relationship("Answer", back_populates="interview", cascade="all, delete-orphan")

