"""
storage.py
In-memory data store standing in for a real database.
Holds: active sessions (Conversation Memory Agent's working state),
finalized session records (feed the Doctor Dashboard), and per-patient
timelines (feed the Symptom Timeline Builder).

Swap this module for a real DB (Postgres/Mongo) in production without
touching any agent logic — agents only call the functions below.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
import itertools
import uuid

_sessions: Dict[str, Dict[str, Any]] = {}          # session_id -> live session state
_finalized: Dict[str, Dict[str, Any]] = {}         # session_id -> finalized record (dashboard feed)
_patient_timelines: Dict[str, List[Dict[str, Any]]] = {}  # patient_id -> list of {date, symptom, summary_ref}


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def create_session(patient_id: str, language: str) -> Dict[str, Any]:
    sid = new_id("sess")
    session = {
        "id": sid,
        "patient_id": patient_id,
        "language": language,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "state": "awaiting_chief_complaint",   # -> awaiting_age -> in_tree -> done
        "chief_complaint_raw": None,
        "symptom": None,
        "tree_qid": None,
        "answers": {},
        "age": None,
        "chat_history": [],   # {role, text, ts}
        "red_flags": [],
        "urgency": None,
        "care_pathway": None,
        "escalate": False,
        "escalate_reasons": [],
        "summary": None,
    }
    _sessions[sid] = session
    return session


def get_session(session_id: str) -> Dict[str, Any]:
    return _sessions.get(session_id)


def log_message(session: Dict[str, Any], role: str, text: str):
    session["chat_history"].append({"role": role, "text": text, "ts": datetime.now(timezone.utc).isoformat()})


def finalize_session(session: Dict[str, Any]):
    """Persist a completed session to the dashboard feed + patient timeline."""
    record = {
        "id": session["id"],
        "patient_id": session["patient_id"],
        "language": session["language"],
        "created_at": session["created_at"],
        "age": session["age"],
        "symptom": session["symptom"],
        "answers": session["answers"],
        "red_flags": session["red_flags"],
        "urgency": session["urgency"],
        "care_pathway": session["care_pathway"],
        "escalate": session["escalate"],
        "escalate_reasons": session["escalate_reasons"],
        "summary": session["summary"],
        "chat_history": session["chat_history"],
    }
    _finalized[session["id"]] = record

    pid = session["patient_id"]
    _patient_timelines.setdefault(pid, [])
    _patient_timelines[pid].append({
        "date": session["created_at"][:10],
        "session_id": session["id"],
        "symptom": session["symptom"],
        "urgency": session["urgency"],
    })
    return record


def all_finalized() -> List[Dict[str, Any]]:
    return sorted(_finalized.values(), key=lambda r: r["created_at"], reverse=True)


def get_finalized(session_id: str):
    return _finalized.get(session_id)


def patient_timeline(patient_id: str) -> List[Dict[str, Any]]:
    return sorted(_patient_timelines.get(patient_id, []), key=lambda e: e["date"])


def population_stats() -> Dict[str, Any]:
    records = list(_finalized.values())
    total = len(records)
    by_symptom: Dict[str, int] = {}
    by_urgency: Dict[str, int] = {}
    for r in records:
        by_symptom[r["symptom"]] = by_symptom.get(r["symptom"], 0) + 1
        by_urgency[r["urgency"]] = by_urgency.get(r["urgency"], 0) + 1
    top_symptoms = sorted(by_symptom.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "total_cases": total,
        "by_symptom": dict(top_symptoms),
        "by_urgency": by_urgency,
        "escalated_count": sum(1 for r in records if r["escalate"]),
    }
