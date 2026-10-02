import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.models.interview import Interview
from app.models.question import Question
from app.schemas.realtime import RealtimeSessionRequest, RealtimeSessionResponse
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/realtime", tags=["Realtime Voice"])


@router.post("/session", response_model=RealtimeSessionResponse)
async def create_realtime_session(
    payload: RealtimeSessionRequest,
    db: Session = Depends(get_db)
):
    """
    SECURE REALTIME SESSION HANDSHAKE:
    The permanent OPENAI_API_KEY remains safely on FastAPI.
    FastAPI calls OpenAI's /v1/realtime/sessions endpoint to mint an ephemeral,
    short-lived client token (client_secret) specifically for this candidate and interview session.
    The browser receives this ephemeral key and establishes a direct WebRTC peer connection.
    """
    interview = db.query(Interview).filter(Interview.id == payload.interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    candidate_name = interview.candidate.name if interview.candidate else "Candidate"

    # Find question context
    question_text = ""
    is_first_question = False
    if payload.question_id:
        question = db.query(Question).filter(Question.id == payload.question_id).first()
        if question:
            question_text = question.question_text
            is_first_question = (question.question_order == 1)
    else:
        # Default to first question or next question
        first_q = db.query(Question).filter(
            Question.interview_id == payload.interview_id,
            Question.question_order == 1
        ).first()
        if first_q:
            question_text = first_q.question_text
            is_first_question = True

    # Call OpenAI Realtime API to generate session
    session_data = await OpenAIService.create_realtime_session(
        interview_id=payload.interview_id,
        candidate_name=candidate_name,
        current_question_text=question_text,
        is_first_question=is_first_question
    )

    client_secret_obj = session_data.get("client_secret", {})
    client_secret_value = client_secret_obj.get("value")
    if not client_secret_value:
        logger.error(f"OpenAI did not return client_secret. Response: {session_data}")
        raise HTTPException(status_code=502, detail="OpenAI did not return a valid client_secret for Realtime audio.")

    return RealtimeSessionResponse(
        client_secret=client_secret_value,
        session_id=session_data.get("id", ""),
        model=session_data.get("model", settings.OPENAI_REALTIME_MODEL),
        voice=session_data.get("voice", settings.OPENAI_VOICE),
        instructions=session_data.get("instructions", "")
    )

