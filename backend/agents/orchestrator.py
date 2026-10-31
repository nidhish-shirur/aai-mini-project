"""Agent 11: Master Orchestrator
Coordinates every other agent turn-by-turn:
extraction -> red-flag-check -> adaptive-question OR finalize -> memory -> safety.
"""
import storage
from knowledge_base import UI_STRINGS, AGE_QUESTION, DISCLAIMER
from agents.symptom_collection import SymptomCollectionAgent
from agents.adaptive_questioning import AdaptiveQuestioningAgent
from agents.medical_knowledge import MedicalKnowledgeAgent
from agents.red_flag_detection import RedFlagDetectionAgent
from agents.risk_assessment import RiskAssessmentAgent
from agents.care_pathway import CarePathwayAgent
from agents.medical_summary import MedicalSummaryAgent
from agents.conversation_memory import ConversationMemoryAgent
from agents.safety_compliance import SafetyComplianceAgent
from agents.escalation import EscalationAgent


class Orchestrator:
    def __init__(self):
        self.symptom_agent = SymptomCollectionAgent()
        self.question_agent = AdaptiveQuestioningAgent()
        self.knowledge_agent = MedicalKnowledgeAgent()
        self.red_flag_agent = RedFlagDetectionAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.pathway_agent = CarePathwayAgent()
        self.summary_agent = MedicalSummaryAgent()
        self.memory_agent = ConversationMemoryAgent()
        self.safety_agent = SafetyComplianceAgent()
        self.escalation_agent = EscalationAgent()

    # ---- session start -------------------------------------------------
    def start_session(self, patient_id: str, language: str):
        session = storage.create_session(patient_id, language)
        greeting = UI_STRINGS["greeting"][language]
        self.memory_agent.log(session, "assistant", greeting)
        return session, greeting

    # ---- per-turn handling ----------------------------------------------
    def handle_message(self, session: dict, text: str):
        lang = session["language"]
        self.memory_agent.log(session, "user", text)

        # Red-flag scan runs on EVERY message regardless of state
        free_text_flags = self.red_flag_agent.check_free_text(text)
        if free_text_flags:
            session["red_flags"].extend(f for f in free_text_flags if f not in session["red_flags"])

        if session["state"] == "awaiting_chief_complaint":
            return self._handle_chief_complaint(session, text)
        elif session["state"] == "awaiting_age":
            return self._handle_age(session, text)
        elif session["state"] == "in_tree":
            return self._handle_tree_answer(session, text)
        elif session["state"] == "done":
            msg = "This session is complete. Please start a new session for a new concern."
            return self._respond(session, msg, done=True)
        else:
            return self._respond(session, "Something went wrong -- please restart.", done=True)

    # ---- state handlers ---------------------------------------------------
    def _handle_chief_complaint(self, session, text):
        session["chief_complaint_raw"] = text
        session["symptom"] = self.symptom_agent.extract_symptom(text)

        if session["red_flags"]:
            return self._finalize(session)

        session["state"] = "awaiting_age"
        msg = AGE_QUESTION[session["language"]]
        return self._respond(session, msg, done=False)

    
    def _handle_age(self, session, text):
        lang = session["language"]
        text = text.strip()

        if not text.isdigit():
            message = {
                "en": "Please enter your age as a number.",
                "hi": "कृपया अपनी उम्र अंकों में दर्ज करें।"
            }
            return self._respond(session, message[lang], done=False)

        age = int(text)

        if age < 0 or age > 120:
            message = {
                "en": "Please enter a valid age between 0 and 120.",
                "hi": "कृपया 0 से 120 के बीच सही उम्र दर्ज करें।"
            }
            return self._respond(session, message[lang], done=False)

        session["age"] = age

        if session["red_flags"]:
            return self._finalize(session)

        qid, node = self.question_agent.first_question(session["symptom"])
        session["tree_qid"] = qid
        session["state"] = "in_tree"

        return self._respond(
            session,
            node["text"][lang],
            done=False
        )

    
    def _handle_tree_answer(self, session, text):
        symptom = session["symptom"]
        current_qid = session["tree_qid"]

        from knowledge_base import QUESTION_TREES

        current_node = QUESTION_TREES.get(
            symptom, QUESTION_TREES["generic"]
        )[current_qid]

        if current_node["type"] == "yesno":
            normalized = self.question_agent.normalize_yesno(text)

            if normalized not in ("yes", "no"):
                message = {
                    "en": "Please answer Yes or No.",
                    "hi": "कृपया हाँ या नहीं में उत्तर दें।"
                }

                return self._respond(
                    session,
                    message[session["language"]],
                    done=False
                )

        field = current_node["field"]

        try:
            next_qid, next_node, stored_value = (
                self.question_agent.next_question(
                    symptom, current_qid, text
                )
            )

        except ValueError as error:
            return self._respond(
                session,
                str(error),
                done=False
            )

        session["answers"][field] = stored_value

        answer_flags = self.red_flag_agent.check_answer(
            symptom, field, stored_value
        )

        if answer_flags:
            session["red_flags"].extend(
                flag for flag in answer_flags
                if flag not in session["red_flags"]
            )
            return self._finalize(session)

        if next_qid is None:
            return self._finalize(session)

        session["tree_qid"] = next_qid

        return self._respond(
            session,
            next_node["text"][session["language"]],
            done=False
        )


    # ---- finalize ----------------------------------------------------------
    def _finalize(self, session):
        lang = session["language"]
        signals = self.knowledge_agent.detect_signals(session["symptom"], session["answers"])
        risk = self.risk_agent.assess(session["answers"], session["age"], signals, session["red_flags"])
        session["urgency"] = risk["urgency"]

        pathway_text = self.pathway_agent.recommend(risk["urgency"], lang)
        session["care_pathway"] = pathway_text

        esc = self.escalation_agent.evaluate(risk["urgency"], session["symptom"], session["answers"], session["red_flags"])
        session["escalate"] = esc["escalate"]
        session["escalate_reasons"] = esc["reasons"]

        summary = self.summary_agent.build(session, risk["urgency"], risk["score"], risk["reasons"], pathway_text)
        session["summary"] = summary
        session["state"] = "done"

        from knowledge_base import URGENCY_LABEL_TRANSLATIONS

        urgency_label = URGENCY_LABEL_TRANSLATIONS[lang][risk["urgency"]]

        if lang == "hi":
            msg = f"तत्कालता का स्तर: {urgency_label}।\n{pathway_text}"
        else:
            msg = f"Urgency: {urgency_label}.\n{pathway_text}"

        if session["escalate"]:
            msg += f"\n\n{UI_STRINGS['escalated'][lang]}"

        response = self._respond(session, msg, done=True)

        storage.finalize_session(session)

        return response

    # ---- shared response builder --------------------------------------------
    def _respond(self, session, message: str, done: bool):
        safe_message = self.safety_agent.sanitize(message)
        if done:
            safe_message = self.safety_agent.with_disclaimer(safe_message)
        self.memory_agent.log(session, "assistant", safe_message)

        return {
            "session_id": session["id"],
            "message": safe_message,
            "done": done,
            "state": session["state"],
            "urgency": session.get("urgency"),
            "care_pathway": session.get("care_pathway"),
            "red_flags": session.get("red_flags") or [],
            "escalate": session.get("escalate"),
            "summary": session.get("summary"),
            "disclaimer": DISCLAIMER if done else None,
        }
