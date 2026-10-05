import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.interview import Interview
from app.models.question import Question
from app.models.answer import Answer
from app.schemas.answer import AnswerEvaluation, AnswerSubmitResponse
from app.schemas.question import QuestionResponse
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class AnswerEvaluatorService:
    @staticmethod
    async def evaluate_and_progress(
        db: Session,
        interview: Interview,
        question: Question,
        transcript: str,
        duration_seconds: Optional[float] = None
    ) -> AnswerSubmitResponse:
        """
        Evaluate candidate's answer, persist the answer and evaluation,
        manage adaptive follow-ups according to limits, and determine the next step.
        """
        candidate = interview.candidate
        profile_json = candidate.profile_json or {}
        skills = profile_json.get("skills", [])
        projects = profile_json.get("projects", [])

        # 1. AI Evaluation (Bypass external API if candidate explicitly skipped the question)
        is_skipped = (
            "[Candidate skipped this question]" in transcript
            or transcript.strip().lower() in ["skip", "skipped", "skip question", "skip this question", "[candidate skipped this question]"]
        )

        if is_skipped:
            evaluation = AnswerEvaluation(
                score=0,
                accuracy_score=0,
                completeness_score=0,
                depth_score=0,
                communication_score=0,
                strengths=[],
                weaknesses=["Candidate chose to skip this question."],
                missing_points=["No spoken response was provided."],
                feedback="Question was skipped by candidate.",
                needs_follow_up=False,
                suggested_follow_up_question=None
            )
        else:
            evaluation = await OpenAIService.evaluate_answer(
                candidate_skills=skills,
                candidate_projects=projects,
                category=question.category,
                question_text=question.question_text,
                expected_topics=question.expected_topics_json or [],
                skills_tested=question.skills_tested_json or [],
                transcript=transcript
            )

        # 2. Persist Answer
        answer = Answer(
            question_id=question.id,
            interview_id=interview.id,
            transcript=transcript,
            duration_seconds=duration_seconds,
            evaluation_json=evaluation.model_dump()
        )
        db.add(answer)
        interview.completed_questions = (interview.completed_questions or 0) + 1
        db.commit()
        db.refresh(answer)

        # 3. Controlled Follow-up logic
        # Rule: Max 1 follow-up per main question, and do not exceed interview.total_questions + 3
        existing_followups_for_this_question = db.query(Question).filter(
            Question.parent_question_id == (question.parent_question_id or question.id)
        ).count()

        total_questions_in_interview = db.query(Question).filter(
            Question.interview_id == interview.id
        ).count()

        follow_up_created: Optional[Question] = None

        if (
            evaluation.needs_follow_up
            and evaluation.suggested_follow_up_question
            and existing_followups_for_this_question < 1
            and total_questions_in_interview < (interview.total_questions + 3)
        ):
            # Insert a follow-up question right after current question
            next_order = question.question_order + 1
            
            # Shift orders of subsequent questions by 1 to make room
            subsequent_questions = db.query(Question).filter(
                Question.interview_id == interview.id,
                Question.question_order >= next_order
            ).all()
            for sq in subsequent_questions:
                sq.question_order += 1

            follow_up_created = Question(
                interview_id=interview.id,
                question_order=next_order,
                category=question.category,
                question_text=evaluation.suggested_follow_up_question,
                skills_tested_json=question.skills_tested_json,
                difficulty=question.difficulty,
                expected_topics_json=question.expected_topics_json,
                is_follow_up=True,
                parent_question_id=question.id
            )
            db.add(follow_up_created)
            interview.total_questions += 1
            db.commit()
            db.refresh(follow_up_created)
            logger.info(f"Created adaptive follow-up question for interview {interview.id}: {follow_up_created.question_text}")

        # 4. Find the next question (unanswered question with the lowest question_order)
        answered_question_ids = [
            a.question_id for a in db.query(Answer.question_id).filter(Answer.interview_id == interview.id).all()
        ]

        next_q = db.query(Question).filter(
            Question.interview_id == interview.id,
            ~Question.id.in_(answered_question_ids)
        ).order_by(Question.question_order.asc()).first()

        is_completed = (next_q is None)

        if is_completed:
            interview.status = "completed"
            db.commit()

        next_question_schema = None
        if next_q:
            next_question_schema = QuestionResponse(
                id=next_q.id,
                interview_id=next_q.interview_id,
                question_order=next_q.question_order,
                category=next_q.category,
                question_text=next_q.question_text,
                skills_tested=next_q.skills_tested_json or [],
                difficulty=next_q.difficulty,
                expected_topics=next_q.expected_topics_json or [],
                is_follow_up=next_q.is_follow_up,
                parent_question_id=next_q.parent_question_id,
                created_at=next_q.created_at
            )

        follow_up_schema = None
        if follow_up_created:
            follow_up_schema = QuestionResponse(
                id=follow_up_created.id,
                interview_id=follow_up_created.interview_id,
                question_order=follow_up_created.question_order,
                category=follow_up_created.category,
                question_text=follow_up_created.question_text,
                skills_tested=follow_up_created.skills_tested_json or [],
                difficulty=follow_up_created.difficulty,
                expected_topics=follow_up_created.expected_topics_json or [],
                is_follow_up=follow_up_created.is_follow_up,
                parent_question_id=follow_up_created.parent_question_id,
                created_at=follow_up_created.created_at
            )

        return AnswerSubmitResponse(
            answer_id=answer.id,
            evaluation=evaluation,
            follow_up_question=follow_up_schema,
            next_question=next_question_schema,
            is_interview_completed=is_completed,
            completed_questions=interview.completed_questions,
            total_questions=interview.total_questions
        )

