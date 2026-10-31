"""Agent 9: Safety & Compliance Agent
Sanitizes any outbound text so the system never states a diagnosis.
This runs on every single message before it is returned to the user."""
from knowledge_base import BANNED_PATTERNS, SAFE_REPLACEMENT, DISCLAIMER


class SafetyComplianceAgent:
    def sanitize(self, text: str) -> str:
        lowered = text.lower()
        for pattern in BANNED_PATTERNS:
            if pattern in lowered:
                return SAFE_REPLACEMENT
        return text

    def with_disclaimer(self, text: str) -> str:
        return f"{text}\n\n{DISCLAIMER}"
