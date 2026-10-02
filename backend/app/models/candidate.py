import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    resume_filename = Column(String(255), nullable=False)
    resume_text = Column(Text, nullable=False)
    profile_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")

