import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.interview import Interview
from app.models.question import Question
from app.models.answer import Answer
from app.schemas.report import FinalInterviewReport
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class ReportGeneratorService:
    @staticmethod
    async def generate_interview_report(
        db: Session,
        interview_id: str
    ) -> FinalInterviewReport:
        """
        Aggregate all question-answer pairs and evaluations to generate the final comprehensive report.
        Stores the report in PostgreSQL and updates the interview record.
        """
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        # If already generated, return cached report
        if interview.final_report_json:
            return FinalInterviewReport(**interview.final_report_json)

        candidate = interview.candidate
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate record missing for interview")

        # Fetch questions and corresponding answers
        questions = db.query(Question).filter(Question.interview_id == interview_id).order_by(Question.question_order.asc()).all()
        answers = db.query(Answer).filter(Answer.interview_id == interview_id).all()
        answers_by_qid = {a.question_id: a for a in answers}

        qa_history: List[Dict[str, Any]] = []
        for q in questions:
            ans = answers_by_qid.get(q.id)
            if ans:
                eval_data = ans.evaluation_json or {}
                qa_history.append({
                    "order": q.question_order,
                    "category": q.category,
                    "question": q.question_text,
                    "candidate_answer": ans.transcript,
                    "score": eval_data.get("score", 70),
                    "strengths": eval_data.get("strengths", []),
                    "missing_points": eval_data.get("missing_points", []),
                    "feedback": eval_data.get("feedback", "No feedback provided.")
                })

        if not qa_history:
            raise HTTPException(
                status_code=400,
                detail="Cannot generate report: No answers have been submitted for this interview yet."
            )

        # Calculate duration
        start_time = interview.started_at or interview.created_at
        end_time = interview.completed_at or datetime.now(timezone.utc)
        duration_minutes = max(1.0, (end_time - start_time).total_seconds() / 60.0)
        interview_date_str = start_time.strftime("%B %d, %Y")

        # Generate report via OpenAI
        report: FinalInterviewReport = await OpenAIService.generate_final_report(
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            interview_date=interview_date_str,
            duration_minutes=duration_minutes,
            qa_history=qa_history
        )

        # Update and persist in DB
        interview.final_report_json = report.model_dump()
        interview.overall_score = float(report.overall_score)
        interview.status = "completed"
        if not interview.completed_at:
            interview.completed_at = end_time

        db.commit()
        db.refresh(interview)

        logger.info(f"Generated and persisted final report for interview {interview_id}. Overall score: {report.overall_score}")
        return report

