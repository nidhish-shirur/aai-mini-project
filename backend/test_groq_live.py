
from agents.symptom_collection import SymptomCollectionAgent

agent = SymptomCollectionAgent()

if agent.client is None:
    print("ERROR: Groq client is not initialized.")
else:
    test_description = (
        "I feel a burning sensation in my chest "
        "and discomfort after eating."
    )

    result = agent.extract_symptom(test_description)

    print("Patient description:", test_description)
    print("Recognized symptom:", result)

    if result != "generic":
        print("LIVE GROQ TEST PASSED")
    else:
        print("Groq returned generic. Check the API response or model configuration.")
