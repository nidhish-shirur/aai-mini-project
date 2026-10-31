
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

TEST_CASES = [
    ("chest_pain", "I have chest pain."),
    ("breathing_difficulty", "I have shortness of breath."),
    ("fever", "I have a fever."),
    ("abdominal_pain", "I have stomach pain."),
    ("headache", "I have a headache."),
    ("cough", "I have been coughing since yesterday."),
    ("bleeding", "I have bleeding that won't stop."),
    ("loss_of_consciousness", "I fainted earlier."),
    ("stroke_symptoms", "My face is drooping."),
    ("injury", "I have an injury."),
]


def api_request(endpoint, method="GET", data=None):
    url = BASE_URL + endpoint

    body = None
    headers = {"Content-Type": "application/json"}

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def run_test(expected_symptom, complaint):
    try:
        # Create a fresh session
        session = api_request(
            "/api/session/start",
            method="POST",
            data={
                "patient_id": None,
                "language": "en"
            }
        )

        session_id = session["session_id"]

        # Submit the symptom description
        api_request(
            f"/api/session/{session_id}/message",
            method="POST",
            data={"text": complaint}
        )

        # Retrieve the stored session
        stored_session = api_request(
            f"/api/session/{session_id}"
        )

        detected_symptom = stored_session.get("symptom")

        passed = detected_symptom == expected_symptom

        return {
            "passed": passed,
            "expected": expected_symptom,
            "detected": detected_symptom,
            "error": None
        }

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        return {
            "passed": False,
            "expected": expected_symptom,
            "detected": None,
            "error": f"HTTP {error.code}: {details}"
        }

    except Exception as error:
        return {
            "passed": False,
            "expected": expected_symptom,
            "detected": None,
            "error": str(error)
        }


def main():
    print("=" * 65)
    print("HEALTHCARE TRIAGE - SYMPTOM RECOGNITION TEST")
    print("=" * 65)

    passed_count = 0
    failed_count = 0

    for expected, complaint in TEST_CASES:
        result = run_test(expected, complaint)

        if result["passed"]:
            passed_count += 1
            status = "PASS"
        else:
            failed_count += 1
            status = "FAIL"

        print(f"\n[{status}] {expected}")
        print(f"  Input:    {complaint}")
        print(f"  Expected: {result['expected']}")
        print(f"  Detected: {result['detected']}")

        if result["error"]:
            print(f"  Error:    {result['error']}")

    print("\n" + "=" * 65)
    print("FINAL TEST SUMMARY")
    print("=" * 65)
    print(f"Total tests : {len(TEST_CASES)}")
    print(f"Passed      : {passed_count}")
    print(f"Failed      : {failed_count}")

    if failed_count == 0:
        print("\nAll symptom recognition tests passed!")
    else:
        print("\nSome symptom recognition tests failed.")

    print("=" * 65)


if __name__ == "__main__":
    main()
