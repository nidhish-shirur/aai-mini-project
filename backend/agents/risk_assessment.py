"""Agent 4: Risk Assessment Agent
Aggregates red flags + clinical signals + severity/duration/age into a
single urgency tier: emergency / urgent / moderate / low."""


class RiskAssessmentAgent:
    def assess(self, answers: dict, age, clinical_signals: list, red_flags: list):
        if red_flags:
            return {"urgency": "emergency", "score": 100, "reasons": red_flags}

        score = 0
        reasons = []

        severity = answers.get("severity")
        if severity is not None:
            try:
                score += min(float(severity), 10) * 5
            except (ValueError, TypeError):
                pass

        for key in ("duration_days",):
            val = answers.get(key)
            if val is not None:
                try:
                    val = float(val)
                    if val >= 5:
                        score += 15
                        reasons.append(f"Prolonged duration ({int(val)} days)")
                    elif val >= 3:
                        score += 8
                except (ValueError, TypeError):
                    pass

        for sig in clinical_signals:
            score += sig["weight"]
            reasons.append(sig["signal"].replace("_", " "))

        if age is not None:
            try:
                age_val = float(age)
                if age_val >= 65 or age_val <= 5:
                    score += 15
                    reasons.append("Age-related vulnerability")
            except (ValueError, TypeError):
                pass

        score = min(score, 100)

        if score >= 70:
            urgency = "urgent"
        elif score >= 40:
            urgency = "moderate"
        else:
            urgency = "low"

        return {"urgency": urgency, "score": round(score, 1), "reasons": reasons}
