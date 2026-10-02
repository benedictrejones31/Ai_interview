from typing import Optional
from pydantic import BaseModel


class RealtimeSessionRequest(BaseModel):
    interview_id: str
    question_id: Optional[str] = None


class RealtimeSessionResponse(BaseModel):
    client_secret: str
    session_id: str
    model: str
    voice: str
    instructions: str

