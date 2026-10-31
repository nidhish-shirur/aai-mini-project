"""Pydantic request/response models."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class StartSessionRequest(BaseModel):
    patient_id: Optional[str] = None   # links multiple sessions -> timeline across visits
    language: str = "en"               # "en" or "hi"


class StartSessionResponse(BaseModel):
    session_id: str
    patient_id: str
    message: str
    done: bool = False


class MessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    session_id: str
    message: str
    done: bool
    state: str
    urgency: Optional[str] = None
    care_pathway: Optional[str] = None
    red_flags: Optional[List[str]] = None
    escalate: Optional[bool] = None
    summary: Optional[Dict[str, Any]] = None
    disclaimer: Optional[str] = None
