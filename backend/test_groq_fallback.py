
from agents.symptom_collection import SymptomCollectionAgent


agent = SymptomCollectionAgent()


# Replace the Groq API method with a controlled test response.
class MockMessage:
    content = '{"symptom": "fever"}'


class MockChoice:
    message = MockMessage()


class MockResponse:
    choices = [MockChoice()]


agent.client.chat.completions.create = lambda **kwargs: MockResponse()


# This description should not match an existing keyword.
result = agent.extract_symptom(
    "An unusual description with no matching keywords"
)

print("Groq fallback validation:", result)

assert result == "fever", "Fallback validation failed!"

print("TEST PASSED")
