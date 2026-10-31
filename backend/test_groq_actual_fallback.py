
from agents.symptom_collection import SymptomCollectionAgent
from knowledge_base import SYMPTOM_KEYWORDS


def test_actual_groq_fallback():
    agent = SymptomCollectionAgent()

    if agent.client is None:
        print("FAILED: Groq client is not initialized.")
        return

    # This description deliberately avoids the existing keywords.
    description = (
        "I feel an uncomfortable squeezing sensation "
        "across my upper torso, especially near the center."
    )

    # Confirm that keyword matching cannot recognize this description.
    text = description.lower().strip()

    keyword_match = any(
        keyword.lower() in text
        for keywords in SYMPTOM_KEYWORDS.values()
        for keyword in keywords
    )

    print("Keyword match:", keyword_match)

    if keyword_match:
        print("FAILED: Test description matched an existing keyword.")
        return

    # Since no keyword matches, the agent must use Groq.
    result = agent.extract_symptom(description)

    print("Groq fallback result:", result)

    if result == "chest_pain":
        print("RESULT: PASSED - Groq fallback successfully identified the symptom.")
    else:
        print("RESULT: FAILED - Expected chest_pain, received:", result)


if __name__ == "__main__":
    test_actual_groq_fallback()
