
"""
main.py -- FastAPI entrypoint for the Healthcare Triage Agent.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload

Then open:
    http://localhost:8000/           -> Patient chat
    http://localhost:8000/dashboard -> Doctor dashboard
    http://localhost:8000/docs      -> Interactive API docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import os

import storage

from models import (
    StartSessionRequest,
    StartSessionResponse,
    MessageRequest,
    MessageResponse
)

from knowledge_base import hospitals_for_urgency, UI_STRINGS
from agents.orchestrator import Orchestrator


app = FastAPI(
    title="Healthcare Triage Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "frontend"
)


# ---------------------------------------------------------------------------
# Patient-facing triage endpoints
# ---------------------------------------------------------------------------

@app.post(
    "/api/session/start",
    response_model=StartSessionResponse
)
def start_session(req: StartSessionRequest):

    patient_id = req.patient_id or storage.new_id("patient")

    session, greeting = orchestrator.start_session(
        patient_id,
        req.language
    )

    return StartSessionResponse(
        session_id=session["id"],
        patient_id=patient_id,
        message=greeting,
        done=False
    )


@app.post("/api/session/{session_id}/message", response_model=MessageResponse)
def send_message(session_id: str, req: MessageRequest):

    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    result = orchestrator.handle_message(
        session,
        req.text
    )

    return MessageResponse(**result)


@app.get("/api/session/{session_id}")
def get_session(session_id: str):

    session = storage.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return session


# ---------------------------------------------------------------------------
# Hospital / care-pathway routing
# Uses the original dummy hospital directory.
# ---------------------------------------------------------------------------

@app.get("/api/hospitals")
def get_hospitals(urgency: str = "low"):

    return {
        "urgency": urgency,
        "options": hospitals_for_urgency(urgency)
    }


# ---------------------------------------------------------------------------
# Doctor Dashboard endpoints
# ---------------------------------------------------------------------------

@app.get("/api/dashboard/sessions")
def dashboard_sessions():

    return storage.all_finalized()


@app.get("/api/dashboard/sessions/{session_id}")
def dashboard_session_detail(session_id: str):

    record = storage.get_finalized(session_id)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Finalized session not found"
        )

    return record


@app.get("/api/dashboard/timeline/{patient_id}")
def dashboard_timeline(patient_id: str):

    """
    Symptom Timeline Builder:
    Aggregates a patient's symptoms across sessions and days.
    """

    return {
        "patient_id": patient_id,
        "timeline": storage.patient_timeline(patient_id)
    }


# ---------------------------------------------------------------------------
# Population Health Analytics
# ---------------------------------------------------------------------------

@app.get("/api/analytics/population")
def population_analytics():

    return storage.population_stats()


# ---------------------------------------------------------------------------
# Frontend static hosting
# ---------------------------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


@app.get("/")
def serve_index():

    return FileResponse(
        os.path.join(FRONTEND_DIR, "index.html")
    )


@app.get("/dashboard")
def serve_dashboard():

    return FileResponse(
        os.path.join(FRONTEND_DIR, "dashboard.html")
    )
