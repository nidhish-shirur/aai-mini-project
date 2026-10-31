"""Agent 10: Escalation Agent
Decides whether a case needs a human clinician's review -- distinct from
urgency: even a 'low' case can need escalation if confidence is low."""


class EscalationAgent:
    def evaluate(self, urgency: str, symptom: str, answers: dict, red_flags: list):
        reasons = []
        if urgency in ("emergency", "urgent"):
            reasons.append(f"Urgency tier is {urgency}")
        if red_flags:
            reasons.append("Red flag symptom(s) present")
        if symptom == "generic":
            reasons.append("Chief complaint did not match a known triage protocol -- needs clinician review")
        if len(answers) < 2:
            reasons.append("Insufficient data collected before session ended")
        return {"escalate": len(reasons) > 0, "reasons": reasons}
