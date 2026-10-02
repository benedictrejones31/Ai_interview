import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from openai import AsyncOpenAI
import httpx

from app.core.config import settings
from app.schemas.candidate import CandidateProfile
from app.schemas.question import QuestionItem, GeneratedQuestionsResponse
from app.schemas.answer import AnswerEvaluation
from app.schemas.report import FinalInterviewReport
from app.prompts.resume_prompts import RESUME_PARSER_SYSTEM_PROMPT, RESUME_PARSER_USER_PROMPT
from app.prompts.question_prompts import QUESTION_GENERATOR_SYSTEM_PROMPT, QUESTION_GENERATOR_USER_PROMPT
from app.prompts.evaluation_prompts import ANSWER_EVALUATION_SYSTEM_PROMPT, ANSWER_EVALUATION_USER_PROMPT
from app.prompts.report_prompts import FINAL_REPORT_SYSTEM_PROMPT, FINAL_REPORT_USER_PROMPT

logger = logging.getLogger(__name__)


class OpenAIService:
    @staticmethod
    def get_client() -> AsyncOpenAI:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key is missing. Please set OPENAI_API_KEY in your backend/.env file."
            )
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @classmethod
    async def extract_candidate_profile(cls, resume_text: str) -> CandidateProfile:
        """Call OpenAI to extract structured candidate profile from raw resume text."""
        client = cls.get_client()
        user_prompt = RESUME_PARSER_USER_PROMPT.format(resume_text=resume_text)

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": RESUME_PARSER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            raw_content = response.choices[0].message.content or "{}"
            parsed_data = json.loads(raw_content)
            return CandidateProfile(**parsed_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error extracting candidate profile: {e}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI service error during resume analysis: {str(e)}"
            )

    @classmethod
    async def generate_interview_questions(
        cls,
        profile: CandidateProfile,
        target_count: int = 12
    ) -> List[QuestionItem]:
        """Generate 10 to 15 customized questions tailored to the candidate's profile."""
        client = cls.get_client()

        user_prompt = QUESTION_GENERATOR_USER_PROMPT.format(
            name=profile.name,
            summary=profile.summary,
            skills=", ".join(profile.skills) if profile.skills else "Not specified",
            projects=json.dumps(profile.projects, indent=2),
            experience=json.dumps(profile.experience, indent=2),
            education=json.dumps(profile.education, indent=2)
        )

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": QUESTION_GENERATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            raw_content = response.choices[0].message.content or "{}"
            data = json.loads(raw_content)
            
            # Accommodate variations in JSON wrapping
            questions_raw = data.get("questions", [])
            if not questions_raw and isinstance(data, list):
                questions_raw = data

            # Ensure sequential order and schema compliance
            questions: List[QuestionItem] = []
            for i, q in enumerate(questions_raw[:15], start=1):
                questions.append(
                    QuestionItem(
                        order=i,
                        category=q.get("category", "technical_skills"),
                        question=q.get("question", ""),
                        skills_tested=q.get("skills_tested", []),
                        difficulty=q.get("difficulty", "intermediate"),
                        expected_topics=q.get("expected_topics", [])
                    )
                )

            # Ensure minimum question count if needed
            if len(questions) < 10:
                logger.warning(f"OpenAI returned only {len(questions)} questions; using returned set.")

            return questions
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating questions: {e}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI service error during question generation: {str(e)}"
            )

    @classmethod
    async def evaluate_answer(
        cls,
        candidate_skills: List[str],
        candidate_projects: List[Dict[str, Any]],
        category: str,
        question_text: str,
        expected_topics: List[str],
        skills_tested: List[str],
        transcript: str
    ) -> AnswerEvaluation:
        """Evaluate candidate's spoken response against expected topics and technical rigor."""
        client = cls.get_client()

        user_prompt = ANSWER_EVALUATION_USER_PROMPT.format(
            skills=", ".join(candidate_skills) if candidate_skills else "General",
            projects=json.dumps(candidate_projects, indent=2),
            category=category,
            question_text=question_text,
            expected_topics=", ".join(expected_topics) if expected_topics else "General principles",
            skills_tested=", ".join(skills_tested) if skills_tested else "General knowledge",
            transcript=transcript
        )

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": ANSWER_EVALUATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw_content = response.choices[0].message.content or "{}"
            data = json.loads(raw_content)

            # Enforce constraints
            score = max(0, min(100, int(data.get("score", 75))))
            return AnswerEvaluation(
                score=score,
                correctness=max(1, min(10, int(data.get("correctness", 7)))),
                relevance=max(1, min(10, int(data.get("relevance", 8)))),
                technical_depth=max(1, min(10, int(data.get("technical_depth", 7)))),
                clarity=max(1, min(10, int(data.get("clarity", 8)))),
                strengths=data.get("strengths", ["Answer addressed the main question."]),
                missing_points=data.get("missing_points", []),
                feedback=data.get("feedback", "Good explanation."),
                needs_follow_up=bool(data.get("needs_follow_up", False)),
                suggested_follow_up_question=data.get("suggested_follow_up_question")
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI service error during answer evaluation: {str(e)}"
            )

    @classmethod
    async def generate_final_report(
        cls,
        candidate_name: str,
        candidate_email: Optional[str],
        interview_date: str,
        duration_minutes: float,
        qa_history: List[Dict[str, Any]]
    ) -> FinalInterviewReport:
        """Synthesize candidate's complete interview into a comprehensive final report."""
        client = cls.get_client()

        formatted_qa = json.dumps(qa_history, indent=2)
        user_prompt = FINAL_REPORT_USER_PROMPT.format(
            name=candidate_name,
            email=candidate_email or "N/A",
            interview_date=interview_date,
            duration_minutes=round(duration_minutes, 1),
            total_questions=len(qa_history),
            qa_history=formatted_qa
        )

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": FINAL_REPORT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw_content = response.choices[0].message.content or "{}"
            data = json.loads(raw_content)

            return FinalInterviewReport(**data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating final report: {e}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI service error during final report synthesis: {str(e)}"
            )

    @classmethod
    async def create_realtime_session(
        cls,
        interview_id: str,
        candidate_name: str,
        current_question_text: str,
        is_first_question: bool = False
    ) -> Dict[str, Any]:
        """
        Request a short-lived ephemeral session token from the OpenAI Realtime REST API.
        The permanent API key stays strictly on FastAPI.
        The returned client_secret.value is given to the frontend for direct WebRTC connection.
        """
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY is not configured on the server."
            )

        instructions = (
            f"You are a professional, polite, and encouraging AI technical interviewer conducting a mock interview with {candidate_name}. "
            "Speak clearly at a natural, professional pace with a warm tone. "
        )
        if is_first_question:
            instructions += (
                "Begin with a brief greeting and instructions: 'Welcome to your AI mock interview! I will guide you through questions tailored to your background. Please answer clearly when you are ready. Let's begin.' "
                f"Then ask the first question: '{current_question_text}'. "
            )
        else:
            instructions += f"Now ask the following question clearly: '{current_question_text}'. "

        instructions += (
            "Wait for the candidate to finish speaking. If the candidate asks you to repeat the question, repeat it politely. "
            "Keep your responses concise, focused, and conversational."
        )

        url = "https://api.openai.com/v1/realtime/sessions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.OPENAI_REALTIME_MODEL,
            "voice": settings.OPENAI_VOICE,
            "instructions": instructions,
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 700
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as http_client:
            try:
                resp = await http_client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"OpenAI Realtime session error: {resp.status_code} - {resp.text}")
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=f"Failed to create Realtime session with OpenAI: {resp.text}"
                    )
                return resp.json()
            except httpx.RequestError as exc:
                logger.error(f"Network error contacting OpenAI Realtime: {exc}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Network error connecting to OpenAI Realtime service: {str(exc)}"
                )

