from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.interview import Interview
from app.models.candidate import Candidate


class AdminInterviewSummary(BaseModel):
    id: str
    candidate_id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    resume_filename: str
    status: str
    overall_score: Optional[float] = None
    completed_questions: int
    total_questions: int
    created_at: datetime
    completed_at: Optional[datetime] = None


router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/interviews", response_model=List[AdminInterviewSummary])
def list_interviews(db: Session = Depends(get_db)):
    """List all interviews and candidate summaries for admin evaluation dashboard."""
    interviews = db.query(Interview).join(Candidate).order_by(Interview.created_at.desc()).all()
    results = []
    for it in interviews:
        results.append(
            AdminInterviewSummary(
                id=it.id,
                candidate_id=it.candidate_id,
                candidate_name=it.candidate.name if it.candidate else "Candidate",
                candidate_email=it.candidate.email if it.candidate else None,
                resume_filename=it.candidate.resume_filename if it.candidate else "resume.pdf",
                status=it.status,
                overall_score=it.overall_score,
                completed_questions=it.completed_questions,
                total_questions=it.total_questions,
                created_at=it.created_at,
                completed_at=it.completed_at
            )
        )
    return results

