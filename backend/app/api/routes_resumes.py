import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.models.candidate import Candidate
from app.models.interview import Interview
from app.schemas.candidate import CandidateResponse, CandidateProfile
from app.schemas.question import QuestionResponse
from app.services.pdf_parser import PDFParserService
from app.services.openai_service import OpenAIService
from app.services.question_generator import QuestionGeneratorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    1. Validate and extract text from uploaded resume PDF.
    2. Extract structured candidate profile using OpenAI.
    3. Persist Candidate into PostgreSQL.
    4. Create an Interview session.
    5. Generate 10-15 personalized interview questions and persist them.
    6. Return candidate profile and interview details.
    """
    logger.info(f"Received resume upload: {file.filename}")

    # Step 1: Parse PDF
    resume_text = await PDFParserService.parse_upload_file(
        file=file,
        max_size_mb=settings.MAX_RESUME_SIZE_MB
    )

    # Step 2: OpenAI Profile Extraction
    profile: CandidateProfile = await OpenAIService.extract_candidate_profile(resume_text=resume_text)

    # Step 3: Save Candidate in Database
    candidate = Candidate(
        name=profile.name or "Candidate",
        email=None,  # Or extracted if present in contact info
        resume_filename=file.filename or "resume.pdf",
        resume_text=resume_text,
        profile_json=profile.model_dump()
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # Step 4: Create Initial Interview Record
    interview = Interview(
        candidate_id=candidate.id,
        status="pending",
        total_questions=10,
        completed_questions=0
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # Step 5: Generate Questions Tailored to Resume
    questions = await QuestionGeneratorService.generate_and_save_questions(
        db=db,
        interview_id=interview.id,
        profile=profile,
        target_count=10
    )

    # Update total questions to exact count generated
    interview.total_questions = len(questions)
    db.commit()

    # Prepare response
    question_responses = [
        QuestionResponse(
            id=q.id,
            interview_id=q.interview_id,
            question_order=q.question_order,
            category=q.category,
            question_text=q.question_text,
            skills_tested=q.skills_tested_json or [],
            difficulty=q.difficulty,
            expected_topics=q.expected_topics_json or [],
            is_follow_up=q.is_follow_up,
            parent_question_id=q.parent_question_id,
            created_at=q.created_at
        )
        for q in questions
    ]

    return {
        "candidate": CandidateResponse(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            resume_filename=candidate.resume_filename,
            profile=profile,
            created_at=candidate.created_at
        ),
        "interview_id": interview.id,
        "total_questions": len(questions),
        "questions": question_responses
    }

