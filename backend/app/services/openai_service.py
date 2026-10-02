import json
import logging
import re
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from openai import AsyncOpenAI
import httpx

from app.core.config import settings
from app.schemas.candidate import CandidateProfile
from app.schemas.question import QuestionItem
from app.schemas.answer import AnswerEvaluation
from app.schemas.report import FinalInterviewReport, CategoryScores, QuestionAnalysisItem
from app.prompts.resume_prompts import RESUME_PARSER_SYSTEM_PROMPT, RESUME_PARSER_USER_PROMPT
from app.prompts.question_prompts import QUESTION_GENERATOR_SYSTEM_PROMPT, QUESTION_GENERATOR_USER_PROMPT
from app.prompts.evaluation_prompts import ANSWER_EVALUATION_SYSTEM_PROMPT, ANSWER_EVALUATION_USER_PROMPT
from app.prompts.report_prompts import FINAL_REPORT_SYSTEM_PROMPT, FINAL_REPORT_USER_PROMPT

logger = logging.getLogger(__name__)


class OpenAIService:
    @staticmethod
    def _is_gemini_active() -> bool:
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    @staticmethod
    async def call_gemini_generate(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Direct, native Google Gemini REST API call with JSON Mode."""
        api_key = settings.GEMINI_API_KEY.strip()
        model = settings.GEMINI_MODEL or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(f"Google Gemini API error {resp.status_code}: {resp.text}")
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Google Gemini API returned error: {resp.text}"
                )

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise HTTPException(status_code=502, detail="Google Gemini returned empty response candidates.")

            text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            # Clean markdown codeblocks if Gemini wraps in ```json ... ```
            cleaned = text_content.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)

            return json.loads(cleaned.strip())

    @staticmethod
    def get_openai_client() -> AsyncOpenAI:
        kwargs: Dict[str, Any] = {
            "api_key": settings.OPENAI_API_KEY or "fallback_key",
        }
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        return AsyncOpenAI(**kwargs)

    @staticmethod
    def _is_quota_or_rate_limit_error(e: Exception) -> bool:
        err_str = str(e).lower()
        return any(phrase in err_str for phrase in [
            "429", "insufficient_quota", "credit_balance_exhausted",
            "rate_limit", "quota exceeded", "exceeded your current quota"
        ])

    # -------------------------------------------------------------
    # 1. CANDIDATE PROFILE EXTRACTION
    # -------------------------------------------------------------
    @classmethod
    async def extract_candidate_profile(cls, resume_text: str) -> CandidateProfile:
        """Extract candidate profile using Google Gemini, OpenAI, or smart local fallback."""
        user_prompt = RESUME_PARSER_USER_PROMPT.format(resume_text=resume_text)

        # Path A: Google Gemini
        if cls._is_gemini_active():
            try:
                logger.info(f"Extracting profile with Google Gemini ({settings.GEMINI_MODEL})...")
                parsed_data = await cls.call_gemini_generate(RESUME_PARSER_SYSTEM_PROMPT, user_prompt)
                return CandidateProfile(**parsed_data)
            except Exception as e:
                logger.error(f"Gemini profile extraction failed: {e}", exc_info=True)
                if settings.ENABLE_FREE_FALLBACK:
                    logger.warning("Falling back to local heuristic extraction.")
                    return cls._heuristic_extract_profile(resume_text)
                raise

        # Path B: OpenAI
        try:
            if not settings.OPENAI_API_KEY and settings.ENABLE_FREE_FALLBACK:
                return cls._heuristic_extract_profile(resume_text)

            client = cls.get_openai_client()
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
        except Exception as e:
            if settings.ENABLE_FREE_FALLBACK and cls._is_quota_or_rate_limit_error(e):
                logger.warning(f"OpenAI API quota exhausted. Using free local parser.")
                return cls._heuristic_extract_profile(resume_text)
            logger.error(f"Error extracting candidate profile: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"AI service error during resume analysis: {str(e)}")

    @classmethod
    def _heuristic_extract_profile(cls, resume_text: str) -> CandidateProfile:
        """Built-in Free Heuristic Parser for 100% offline free operation."""
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        candidate_name = "Candidate"
        for line in lines[:5]:
            clean = re.sub(r'[^a-zA-Z\s]', '', line).strip()
            words = clean.split()
            if 1 <= len(words) <= 4 and not any(k in clean.lower() for k in ["resume", "curriculum", "email", "phone"]):
                candidate_name = clean.title()
                break

        known_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI",
            "Django", "Flask", "Go", "Golang", "C++", "Java", "Rust", "SQL", "PostgreSQL",
            "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", "GCP", "Azure",
            "PyTorch", "TensorFlow", "Keras", "Scikit-Learn", "Machine Learning", "Deep Learning",
            "CNN", "RNN", "LSTM", "Vision Transformer", "ViT", "NLP", "LLM", "OpenAI",
            "Computer Vision", "REST API", "GraphQL", "Git", "CI/CD", "Linux", "Tailwind CSS"
        ]
        found_skills = []
        lower_text = resume_text.lower()
        for sk in known_skills:
            if re.search(r'\b' + re.escape(sk.lower()) + r'\b', lower_text):
                found_skills.append(sk)

        return CandidateProfile(
            name=candidate_name,
            summary=f"Software & Machine Learning candidate with background in {', '.join(found_skills[:4]) if found_skills else 'software development'}.",
            skills=found_skills if found_skills else ["Python", "FastAPI", "Full-Stack Development"],
            education=[{"degree": "Bachelor of Science", "field_of_study": "Computer Science / Engineering"}],
            projects=[{
                "title": f"Technical Engineering Systems ({', '.join(found_skills[:3]) if found_skills else 'Software'})",
                "description": "Core software and distributed applications implementation.",
                "technologies": found_skills[:3]
            }],
            experience=[{"role": "Software Engineer", "company": "Technology Organization", "duration": "Recent"}],
            certifications=[],
            target_roles=["Software Engineer", "Machine Learning Engineer"]
        )

    # -------------------------------------------------------------
    # 2. QUESTION GENERATION
    # -------------------------------------------------------------
    @classmethod
    async def generate_interview_questions(
        cls,
        profile: CandidateProfile,
        target_count: int = 12
    ) -> List[QuestionItem]:
        """Generate tailored questions using Google Gemini, OpenAI, or free heuristic engine."""
        user_prompt = QUESTION_GENERATOR_USER_PROMPT.format(
            name=profile.name,
            summary=profile.summary,
            skills=", ".join(profile.skills) if profile.skills else "Not specified",
            projects=json.dumps(profile.projects, indent=2),
            experience=json.dumps(profile.experience, indent=2),
            education=json.dumps(profile.education, indent=2)
        )

        # Path A: Google Gemini
        if cls._is_gemini_active():
            try:
                logger.info(f"Generating questions with Google Gemini ({settings.GEMINI_MODEL})...")
                data = await cls.call_gemini_generate(QUESTION_GENERATOR_SYSTEM_PROMPT, user_prompt)
                questions_raw = data.get("questions", [])
                if not questions_raw and isinstance(data, list):
                    questions_raw = data

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
                if questions:
                    return questions
            except Exception as e:
                logger.error(f"Gemini question generation error: {e}", exc_info=True)
                if settings.ENABLE_FREE_FALLBACK:
                    return cls._heuristic_generate_questions(profile, target_count)
                raise

        # Path B: OpenAI
        try:
            if not settings.OPENAI_API_KEY and settings.ENABLE_FREE_FALLBACK:
                return cls._heuristic_generate_questions(profile, target_count)

            client = cls.get_openai_client()
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
            questions_raw = data.get("questions", [])
            if not questions_raw and isinstance(data, list):
                questions_raw = data

            questions = []
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
            if questions:
                return questions
            return cls._heuristic_generate_questions(profile, target_count)
        except Exception as e:
            if settings.ENABLE_FREE_FALLBACK and cls._is_quota_or_rate_limit_error(e):
                logger.warning(f"OpenAI API quota exhausted. Using free question generator.")
                return cls._heuristic_generate_questions(profile, target_count)
            logger.error(f"Error generating questions: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"Question generation failed: {str(e)}")

    @classmethod
    def _heuristic_generate_questions(cls, profile: CandidateProfile, target_count: int = 12) -> List[QuestionItem]:
        """Free questions based on candidate resume data."""
        skills = profile.skills or ["Python", "FastAPI", "Databases"]
        primary = skills[0] if len(skills) > 0 else "Python"
        secondary = skills[1] if len(skills) > 1 else "FastAPI"
        tertiary = skills[2] if len(skills) > 2 else "PostgreSQL"
        project_title = profile.projects[0]["title"] if profile.projects else "Engineering Systems"

        template_questions = [
            {
                "order": 1,
                "category": "introduction",
                "question": f"Welcome {profile.name}! To get started, please tell me about yourself and an overview of your technical background.",
                "skills_tested": ["communication", "career_overview"],
                "difficulty": "basic",
                "expected_topics": ["background", "education", "key technical interests"]
            },
            {
                "order": 2,
                "category": "resume",
                "question": f"Looking at your resume, what sparked your interest in working with {primary} and building modern software architectures?",
                "skills_tested": ["motivation", "foundations"],
                "difficulty": "basic",
                "expected_topics": ["career milestones", "engineering passion"]
            },
            {
                "order": 3,
                "category": "technical_skills",
                "question": f"Can you explain how you use {primary} in production environments, and what best practices you follow for maintainability and testing?",
                "skills_tested": [primary, "best_practices"],
                "difficulty": "intermediate",
                "expected_topics": ["architecture", "code quality", "error handling"]
            },
            {
                "order": 4,
                "category": "technical_skills",
                "question": f"You also listed experience with {secondary}. How do you handle concurrency, asynchronous execution, and performance optimization when using it?",
                "skills_tested": [secondary, "performance"],
                "difficulty": "intermediate",
                "expected_topics": ["async/await", "throughput", "resource management"]
            },
            {
                "order": 5,
                "category": "projects",
                "question": f"Could you walk me through your project '{project_title}'? What was the overall architecture and what specific role did you play?",
                "skills_tested": ["system_design", "project_delivery"],
                "difficulty": "intermediate",
                "expected_topics": ["problem statement", "architecture", "trade-offs"]
            },
            {
                "order": 6,
                "category": "projects",
                "question": f"What was the most challenging technical roadblock you encountered while developing '{project_title}', and how did you resolve it?",
                "skills_tested": ["troubleshooting", "problem_solving"],
                "difficulty": "advanced",
                "expected_topics": ["debugging", "root cause analysis", "resilience"]
            },
            {
                "order": 7,
                "category": "experience",
                "question": f"In your experience working with {tertiary}, how do you ensure data integrity, indexing efficiency, and schema versioning over time?",
                "skills_tested": [tertiary, "data_modeling"],
                "difficulty": "intermediate",
                "expected_topics": ["database indexing", "migrations", "consistency"]
            },
            {
                "order": 8,
                "category": "problem_solving",
                "question": "Imagine an API endpoint you deployed experiences an unexpected 10x surge in traffic and latency spikes dramatically. What steps do you take to diagnose and remediate the bottleneck?",
                "skills_tested": ["system_reliability", "incident_response"],
                "difficulty": "advanced",
                "expected_topics": ["metrics", "profiling", "caching", "rate limiting"]
            },
            {
                "order": 9,
                "category": "behavioral",
                "question": "Can you describe a situation where you had a disagreement with a team member over a technical decision or design pattern? How did you reach alignment?",
                "skills_tested": ["collaboration", "communication"],
                "difficulty": "intermediate",
                "expected_topics": ["constructive debate", "code reviews", "team empathy"]
            },
            {
                "order": 10,
                "category": "behavioral",
                "question": "How do you stay up-to-date with emerging tools, libraries, and frameworks, and how do you decide when to adopt a new technology in a production project?",
                "skills_tested": ["continuous_learning", "technical_discernment"],
                "difficulty": "basic",
                "expected_topics": ["evaluation criteria", "prototyping", "learning strategy"]
            },
            {
                "order": 11,
                "category": "technical_skills",
                "question": f"How do you approach writing comprehensive automated tests for your services, and what metrics or principles do you prioritize?",
                "skills_tested": ["testing", "CI/CD"],
                "difficulty": "intermediate",
                "expected_topics": ["unit tests", "integration tests", "mocking"]
            },
            {
                "order": 12,
                "category": "behavioral",
                "question": "Looking forward, what kind of technical challenges or architectural areas are you most excited to tackle in your next role?",
                "skills_tested": ["vision", "growth_mindset"],
                "difficulty": "basic",
                "expected_topics": ["career aspirations", "technical interests"]
            }
        ]
        return [QuestionItem(**q) for q in template_questions[:target_count]]

    # -------------------------------------------------------------
    # 3. ANSWER EVALUATION
    # -------------------------------------------------------------
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
        """Evaluate candidate answer using Google Gemini, OpenAI, or free engine."""
        user_prompt = ANSWER_EVALUATION_USER_PROMPT.format(
            skills=", ".join(candidate_skills) if candidate_skills else "General",
            projects=json.dumps(candidate_projects, indent=2),
            category=category,
            question_text=question_text,
            expected_topics=", ".join(expected_topics) if expected_topics else "General principles",
            skills_tested=", ".join(skills_tested) if skills_tested else "General knowledge",
            transcript=transcript
        )

        # Path A: Google Gemini
        if cls._is_gemini_active():
            try:
                logger.info(f"Evaluating answer with Google Gemini ({settings.GEMINI_MODEL})...")
                data = await cls.call_gemini_generate(ANSWER_EVALUATION_SYSTEM_PROMPT, user_prompt)
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
            except Exception as e:
                logger.error(f"Gemini evaluation error: {e}", exc_info=True)
                if settings.ENABLE_FREE_FALLBACK:
                    return cls._heuristic_evaluate_answer(category, question_text, expected_topics, transcript)
                raise

        # Path B: OpenAI
        try:
            if not settings.OPENAI_API_KEY and settings.ENABLE_FREE_FALLBACK:
                return cls._heuristic_evaluate_answer(category, question_text, expected_topics, transcript)

            client = cls.get_openai_client()
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
        except Exception as e:
            if settings.ENABLE_FREE_FALLBACK and cls._is_quota_or_rate_limit_error(e):
                return cls._heuristic_evaluate_answer(category, question_text, expected_topics, transcript)
            logger.error(f"Error evaluating answer: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"Answer evaluation failed: {str(e)}")

    @classmethod
    def _heuristic_evaluate_answer(
        cls,
        category: str,
        question_text: str,
        expected_topics: List[str],
        transcript: str
    ) -> AnswerEvaluation:
        words = transcript.strip().split()
        word_count = len(words)
        base_score = 70
        if word_count > 60:
            base_score += 15
        elif word_count > 30:
            base_score += 10
        elif word_count < 10:
            base_score -= 20

        matched_topics = [t for t in expected_topics if t.lower() in transcript.lower()]
        base_score += min(15, len(matched_topics) * 5)
        final_score = max(40, min(95, base_score))

        needs_follow_up = (word_count < 25 and category in ["technical_skills", "projects"])
        suggested_follow_up = None
        if needs_follow_up:
            suggested_follow_up = "Could you elaborate more on the specific architectural decisions or trade-offs you made in that scenario?"

        return AnswerEvaluation(
            score=final_score,
            correctness=max(5, min(10, final_score // 10)),
            relevance=max(6, min(10, (final_score + 5) // 10)),
            technical_depth=max(5, min(10, (final_score - 5) // 10)),
            clarity=8,
            strengths=[
                "Directly addressed the question asked",
                "Demonstrated relevant technical context in response"
            ],
            missing_points=[
                "Could elaborate further on quantitative benchmarks or specific error scenarios"
            ] if word_count < 40 else [],
            feedback="Clear response with solid technical foundations. Expanding on quantitative metrics will add further impact.",
            needs_follow_up=needs_follow_up,
            suggested_follow_up_question=suggested_follow_up
        )

    # -------------------------------------------------------------
    # 4. FINAL REPORT GENERATION
    # -------------------------------------------------------------
    @classmethod
    async def generate_final_report(
        cls,
        candidate_name: str,
        candidate_email: Optional[str],
        interview_date: str,
        duration_minutes: float,
        qa_history: List[Dict[str, Any]]
    ) -> FinalInterviewReport:
        """Synthesize final report using Google Gemini, OpenAI, or free engine."""
        formatted_qa = json.dumps(qa_history, indent=2)
        user_prompt = FINAL_REPORT_USER_PROMPT.format(
            name=candidate_name,
            email=candidate_email or "N/A",
            interview_date=interview_date,
            duration_minutes=round(duration_minutes, 1),
            total_questions=len(qa_history),
            qa_history=formatted_qa
        )

        # Path A: Google Gemini
        if cls._is_gemini_active():
            try:
                logger.info(f"Synthesizing final report with Google Gemini ({settings.GEMINI_MODEL})...")
                data = await cls.call_gemini_generate(FINAL_REPORT_SYSTEM_PROMPT, user_prompt)
                return FinalInterviewReport(**data)
            except Exception as e:
                logger.error(f"Gemini report synthesis error: {e}", exc_info=True)
                if settings.ENABLE_FREE_FALLBACK:
                    return cls._heuristic_generate_report(candidate_name, candidate_email, interview_date, duration_minutes, qa_history)
                raise

        # Path B: OpenAI
        try:
            if not settings.OPENAI_API_KEY and settings.ENABLE_FREE_FALLBACK:
                return cls._heuristic_generate_report(candidate_name, candidate_email, interview_date, duration_minutes, qa_history)

            client = cls.get_openai_client()
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
        except Exception as e:
            if settings.ENABLE_FREE_FALLBACK and cls._is_quota_or_rate_limit_error(e):
                return cls._heuristic_generate_report(candidate_name, candidate_email, interview_date, duration_minutes, qa_history)
            logger.error(f"Error generating final report: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"Final report generation failed: {str(e)}")

    @classmethod
    def _heuristic_generate_report(
        cls,
        candidate_name: str,
        candidate_email: Optional[str],
        interview_date: str,
        duration_minutes: float,
        qa_history: List[Dict[str, Any]]
    ) -> FinalInterviewReport:
        scores = [item.get("score", 75) for item in qa_history]
        avg_score = round(sum(scores) / len(scores)) if scores else 80

        question_analyses = []
        for item in qa_history:
            question_analyses.append(
                QuestionAnalysisItem(
                    question=item.get("question", ""),
                    category=item.get("category", "technical_skills"),
                    candidate_answer=item.get("candidate_answer", ""),
                    score=item.get("score", 75),
                    strengths=item.get("strengths", ["Answer addressed the key concept"]),
                    missing_points=item.get("missing_points", []),
                    feedback=item.get("feedback", "Good engineering response.")
                )
            )

        return FinalInterviewReport(
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            interview_date=interview_date,
            duration_minutes=round(duration_minutes, 1),
            total_questions_asked=len(qa_history),
            overall_score=avg_score,
            category_scores=CategoryScores(
                technical_knowledge=min(100, avg_score + 2),
                project_understanding=min(100, avg_score + 4),
                problem_solving=max(50, avg_score - 3),
                communication_clarity=min(100, avg_score + 1),
                resume_understanding=min(100, avg_score + 5)
            ),
            strengths=[
                f"{candidate_name} demonstrated strong understanding of software engineering fundamentals.",
                "Provided coherent architectural explanations for highlighted projects.",
                "Communicated technical decisions effectively across the interview session."
            ],
            areas_for_improvement=[
                "Include more quantitative benchmarks (e.g. latency percentiles, throughput metrics) when describing outcomes.",
                "Deepen discussion on edge-case error handling in distributed systems."
            ],
            question_analyses=question_analyses,
            final_summary=f"Candidate {candidate_name} completed {len(qa_history)} technical questions with an overall score of {avg_score}/100. Demonstrated solid proficiency across technical concepts and project delivery.",
            recommendation="Human Review Recommended"
        )

    # -------------------------------------------------------------
    # 5. REALTIME SESSION HANDSHAKE
    # -------------------------------------------------------------
    @classmethod
    async def create_realtime_session(
        cls,
        interview_id: str,
        candidate_name: str,
        current_question_text: str,
        is_first_question: bool = False
    ) -> Dict[str, Any]:
        """
        Request ephemeral session token if OpenAI is active, or trigger
        the browser's built-in Web Speech API voice (which is 100% free of charge).
        """
        if not settings.OPENAI_API_KEY or cls._is_gemini_active():
            # If user uses Gemini or no OpenAI key, use browser's built-in voice
            raise HTTPException(
                status_code=503,
                detail="OpenAI Realtime requires an active OpenAI key. Using browser voice synthesis fallback."
            )

        instructions = (
            f"You are a professional AI technical interviewer conducting a mock interview with {candidate_name}. "
            "Speak clearly at a natural pace. "
        )
        if is_first_question:
            instructions += (
                "Begin with a brief greeting: 'Welcome to your AI mock interview! Please answer clearly when you are ready. Let's begin.' "
                f"Then ask the first question: '{current_question_text}'. "
            )
        else:
            instructions += f"Now ask the following question clearly: '{current_question_text}'. "

        url = "https://api.openai.com/v1/realtime/sessions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.OPENAI_REALTIME_MODEL,
            "voice": settings.OPENAI_VOICE,
            "instructions": instructions,
            "input_audio_transcription": {"model": "whisper-1"},
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
                    raise HTTPException(
                        status_code=resp.status_code,
                        detail=f"OpenAI Realtime session unavailable ({resp.text}). Browser voice fallback activated."
                    )
                return resp.json()
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"Network error connecting to OpenAI Realtime: {str(exc)}"
                )
