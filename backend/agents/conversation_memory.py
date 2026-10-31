"""Agent 8: Conversation Memory Agent
Thin wrapper around storage.py -- tracks turn history within a session
and links sessions to a patient's cross-session timeline."""
import storage


class ConversationMemoryAgent:
    def log(self, session: dict, role: str, text: str):
        storage.log_message(session, role, text)

    def timeline_for(self, patient_id: str):
        return storage.patient_timeline(patient_id)
