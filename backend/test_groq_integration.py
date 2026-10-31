
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"


def api_request(method, endpoint, data=None):
    url = BASE_URL + endpoint

    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8")
        raise Exception(f"HTTP {error.code}: {details}")


def create_session(language):
    response = api_request(
        "POST",
        "/api/session/start",
        {
            "patient_id": None,
            "language": language
        }
    )

    session_id = response.get("session_id") or response.get("id")

    if not session_id:
        raise Exception(f"Session ID missing: {response}")

    return session_id


def send_message(session_id, message):
    return api_request(
        "POST",
        f"/api/session/{session_id}/message",
        {"text": message}
    )


def get_session(session_id):
    return api_request(
        "GET",
        f"/api/session/{session_id}"
    )


def run_test(name, test_function):
    print(f"\n{'=' * 55}")
    print(f"TEST: {name}")
    print("=" * 55)

    try:
        test_function()
        print("RESULT: PASSED")

    except Exception as error:
        print("RESULT: FAILED")
        print("Reason:", error)


def test_english_groq_fallback():
    session_id = create_session("en")

    send_message(
        session_id,
        "I feel a burning sensation in my chest and discomfort after eating."
    )

    session = get_session(session_id)
    symptom = session.get("symptom")

    print("Recognized symptom:", symptom)

    assert symptom == "chest_pain", (
        f"Expected chest_pain, received {symptom}"
    )


def test_hindi_symptom_recognition():
    session_id = create_session("hi")

    send_message(
        session_id,
        "मुझे सिरदर्द हो रहा है"
    )

    session = get_session(session_id)
    symptom = session.get("symptom")

    print("Recognized symptom:", symptom)

    assert symptom == "headache", (
        f"Expected headache, received {symptom}"
    )


def test_emergency_escalation():
    session_id = create_session("en")

    response = send_message(
        session_id,
        "I have severe chest pain and difficulty breathing."
    )

    print("Assessment response:", response.get("message"))
    print("Urgency:", response.get("urgency"))
    print("Escalation:", response.get("escalate"))

    assert response.get("done") is True, (
        "Emergency assessment did not finish"
    )

    assert response.get("escalate") is True, (
        "Emergency escalation did not occur"
    )


if __name__ == "__main__":
    print("GROQ + HEALTHCARE TRIAGE INTEGRATION TESTS")
    print("Backend:", BASE_URL)

    run_test(
        "English Groq fallback through patient API",
        test_english_groq_fallback
    )

    run_test(
        "Hindi symptom recognition through patient API",
        test_hindi_symptom_recognition
    )

    run_test(
        "Emergency detection and escalation",
        test_emergency_escalation
    )
