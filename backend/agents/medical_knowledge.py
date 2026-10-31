"""Agent 3: Medical Knowledge Agent
Applies triage-protocol rules (not diagnosis) to detect clinical signals
from the collected answers -- e.g. chest pain + sweating -> cardiac signal."""
from knowledge_base import CLINICAL_SIGNAL_RULES


class MedicalKnowledgeAgent:
    def detect_signals(self, symptom: str, answers: dict):
        signals = []
        for rule in CLINICAL_SIGNAL_RULES:
            if rule["symptom"] != symptom:
                continue
            if all(str(answers.get(k, "")).lower() == v for k, v in rule["conditions"].items()):
                signals.append({"signal": rule["signal"], "weight": rule["weight"]})
        return signals
