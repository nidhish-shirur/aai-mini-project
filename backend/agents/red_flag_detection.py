"""Agent 5 (spec) / core safety agent: Red Flag Detection Agent
Detects dangerous symptoms that must trigger immediate escalation,
both from raw free text (any turn) and from specific tree answers."""
from knowledge_base import IMMEDIATE_RED_FLAG_SYMPTOMS, RED_FLAG_TRIGGERS, SYMPTOM_KEYWORDS


class RedFlagDetectionAgent:
    def check_free_text(self, raw_text: str):
        """Scan any free-text turn for globally dangerous symptom mentions."""
        text = raw_text.lower()
        flags = []
        for symptom, description in IMMEDIATE_RED_FLAG_SYMPTOMS.items():
            for kw in SYMPTOM_KEYWORDS.get(symptom, []):
                if kw in text:
                    flags.append(description)
                    break
        return flags

    def check_answer(self, symptom: str, field: str, value):
        flags = []
        for trigger in RED_FLAG_TRIGGERS:
            if trigger["symptom"] == symptom and trigger["field"] == field and str(value).lower() == trigger["value"]:
                flags.append(trigger["flag"])
        return flags
