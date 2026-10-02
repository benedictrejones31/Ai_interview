import logging
from typing import List
from sqlalchemy.orm import Session
from app.models.question import Question
from app.schemas.candidate import CandidateProfile
from app.schemas.question import QuestionItem
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class QuestionGeneratorService:
    @staticmethod
    async def generate_and_save_questions(
        db: Session,
        interview_id: str,
        profile: CandidateProfile,
        target_count: int = 12
    ) -> List[Question]:
        """
        Generate questions using OpenAI and persist them to the database.
        """
        question_items: List[QuestionItem] = await OpenAIService.generate_interview_questions(
            profile=profile,
            target_count=target_count
        )

        db_questions: List[Question] = []
        for item in question_items:
            q = Question(
                interview_id=interview_id,
                question_order=item.order,
                category=item.category,
                question_text=item.question,
                skills_tested_json=item.skills_tested,
                difficulty=item.difficulty,
                expected_topics_json=item.expected_topics,
                is_follow_up=False,
                parent_question_id=None
            )
            db.add(q)
            db_questions.append(q)

        db.commit()
        for q in db_questions:
            db.refresh(q)

        logger.info(f"Generated and persisted {len(db_questions)} questions for interview {interview_id}.")
        return db_questions

