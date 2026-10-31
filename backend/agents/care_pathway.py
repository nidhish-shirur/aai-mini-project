"""Agent 6: Care Pathway Agent
Maps an urgency tier to a concrete, non-diagnostic recommended action."""
from knowledge_base import CARE_PATHWAY_MAP


class CarePathwayAgent:
    def recommend(self, urgency: str, language: str = "en") -> str:
        return CARE_PATHWAY_MAP.get(urgency, CARE_PATHWAY_MAP["low"])[language]
