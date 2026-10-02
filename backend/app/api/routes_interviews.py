import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.interview import Interview
from app.models.question import Question
from app.models.candidate import Candidate
from app.schemas.interview import (
    InterviewCreate,
    InterviewResponse,
    InterviewStartResponse,
    InterviewDetailResponse,
)
from app.schemas.candidate import CandidateResponse, CandidateProfile
from app.schemas.question import QuestionResponse
from app.schemas.answer import AnswerSubmitRequest, AnswerSubmitResponse
from app.schemas.report import FinalInterviewReport
from app.services.answer_evaluator import AnswerEvaluatorService
from app.services.report_generator import ReportGeneratorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


@router.post("", response_model=InterviewResponse)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_db)):
    """Create a new interview session for a candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    interview = Interview(
        candidate_id=payload.candidate_id,
        status="pending",
        total_questions=payload.total_questions
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@router.get("/{interview_id}", response_model=InterviewDetailResponse)
def get_interview(interview_id: str, db: Session = Depends(get_db)):
    """Retrieve full details of an interview, including candidate profile and questions."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    candidate = interview.candidate
    candidate_profile = CandidateProfile(**(candidate.profile_json or {}))

    questions = db.query(Question).filter(
        Question.interview_id == interview_id
    ).order_by(Question.question_order.asc()).all()

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

    report = None
    if interview.final_report_json:
        report = FinalInterviewReport(**interview.final_report_json)

    return InterviewDetailResponse(
        id=interview.id,
        candidate_id=interview.candidate_id,
        candidate=CandidateResponse(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            resume_filename=candidate.resume_filename,
            profile=candidate_profile,
            created_at=candidate.created_at
        ),
        status=interview.status,
        started_at=interview.started_at,
        completed_at=interview.completed_at,
        total_questions=interview.total_questions,
        completed_questions=interview.completed_questions,
        overall_score=interview.overall_score,
        questions=question_responses,
        final_report=report,
        created_at=interview.created_at
    )


@router.post("/{interview_id}/start", response_model=InterviewStartResponse)
def start_interview(interview_id: str, db: Session = Depends(get_db)):
    """
    Start the interview session.
    Updates status to 'in_progress', records started_at timestamp, and returns initial instructions + Question 1.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status == "pending":
        interview.status = "in_progress"
        interview.started_at = datetime.now(timezone.utc)
        db.commit()

    first_question = db.query(Question).filter(
        Question.interview_id == interview_id,
        Question.question_order == 1
    ).first()

    if not first_question:
        raise HTTPException(status_code=400, detail="No questions have been generated for this interview.")

    candidate_name = interview.candidate.name if interview.candidate else "Candidate"
    welcome_message = (
        f"Welcome to your AI mock interview, {candidate_name}. "
        "I will ask you approximately 10 to 15 questions based on your resume. "
        "Please answer clearly and honestly. Take a few seconds to think before answering. "
        "If you do not understand a question, you can ask me to repeat it. "
        "Please keep your answers focused. When you're ready, let's begin."
    )

    return InterviewStartResponse(
        interview_id=interview.id,
        candidate_name=candidate_name,
        status=interview.status,
        welcome_message=welcome_message,
        first_question=QuestionResponse(
            id=first_question.id,
            interview_id=first_question.interview_id,
            question_order=first_question.question_order,
            category=first_question.category,
            question_text=first_question.question_text,
            skills_tested=first_question.skills_tested_json or [],
            difficulty=first_question.difficulty,
            expected_topics=first_question.expected_topics_json or [],
            is_follow_up=first_question.is_follow_up,
            parent_question_id=first_question.parent_question_id,
            created_at=first_question.created_at
        )
    )


@router.post("/{interview_id}/answer", response_model=AnswerSubmitResponse)
async def submit_answer(
    interview_id: str,
    payload: AnswerSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Submit candidate's spoken response transcript.
    Evaluates response with AI, determines if follow-up is needed (with strict bounds),
    and returns next question or completion indicator.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    question = db.query(Question).filter(
        Question.id == payload.question_id,
        Question.interview_id == interview_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this interview")

    result: AnswerSubmitResponse = await AnswerEvaluatorService.evaluate_and_progress(
        db=db,
        interview=interview,
        question=question,
        transcript=payload.transcript,
        duration_seconds=payload.duration_seconds
    )
    return result


@router.post("/{interview_id}/complete", response_model=FinalInterviewReport)
async def complete_interview(interview_id: str, db: Session = Depends(get_db)):
    """
    Synthesize all answered questions, compute scores, generate comprehensive report,
    and persist in PostgreSQL.
    """
    report = await ReportGeneratorService.generate_interview_report(
        db=db,
        interview_id=interview_id
    )
    return report


@router.get("/{interview_id}/report", response_model=FinalInterviewReport)
def get_interview_report(interview_id: str, db: Session = Depends(get_db)):
    """Retrieve stored final interview report."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if not interview.final_report_json:
        raise HTTPException(status_code=404, detail="Report has not been generated for this interview yet.")

    return FinalInterviewReport(**interview.final_report_json)

