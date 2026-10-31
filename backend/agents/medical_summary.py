"""Agent 7: Medical Summary Agent
Produces the structured clinical summary a doctor can read in seconds."""
from datetime import datetime, timezone


class MedicalSummaryAgent:
    def build(self, session: dict, urgency: str, urgency_score, reasons, care_pathway_text: str) -> dict:
        return {
            "session_id": session["id"],
            "patient_id": session["patient_id"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "age": session["age"],
            "chief_complaint": session["symptom"],
            "answers": session["answers"],
            "duration_note": self._duration_note(session["answers"]),
            "severity": session["answers"].get("severity"),
            "red_flags": session["red_flags"] or [],
            "urgency": urgency,
            "urgency_score": urgency_score,
            "risk_reasons": reasons,
            "recommended_pathway": care_pathway_text,
        }

    def _duration_note(self, answers: dict) -> str:
        for key in ("duration_days", "duration_minutes", "duration_hours"):
            if key in answers:
                unit = key.split("_")[1]
                return f"{answers[key]} {unit}"
        return "not specified"
