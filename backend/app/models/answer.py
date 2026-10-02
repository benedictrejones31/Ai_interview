import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    interview_id = Column(String(36), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    transcript = Column(Text, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    evaluation_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    question = relationship("Question", back_populates="answers")
    interview = relationship("Interview", back_populates="answers")

