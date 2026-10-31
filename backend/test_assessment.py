"""Automated API tests for the Healthcare Triage Agent.

Run from the backend folder while the FastAPI server is running:
    python test_assessment.py

Optional:
    python test_assessment.py --base-url http://127.0.0.1:8000

Uses only Python's standard library. These are software-behaviour tests with
simulated answers, not clinical validation.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Tuple


class APIError(Exception):
    pass


def request_json(base_url: str, method: str, path: str,
                 payload: Dict[str, Any] | None = None) -> Tuple[int, Any]:
    url = base_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = raw
        raise APIError(f"HTTP {exc.code} for {path}: {body}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise APIError(
            f"Cannot reach {url}. Start the backend with 'python -m uvicorn main:app --reload'. Details: {exc}"
        ) from exc


def start_session(base_url: str) -> Tuple[str, str]:
    status, body = request_json(
        base_url, "POST", "/api/session/start",
        {"patient_id": None, "language": "en"},
    )
    if status != 200 or not body.get("session_id"):
        raise APIError(f"Session creation failed: {body}")
    return body["session_id"], body.get("patient_id", "")


def send(base_url: str, session_id: str, text: str) -> Dict[str, Any]:
    _, body = request_json(
        base_url, "POST", f"/api/session/{session_id}/message", {"text": text}
    )
    return body


def check(condition: bool, description: str, details: str = "") -> Tuple[bool, str, str]:
    return condition, description, details


def run_tests(base_url: str) -> int:
    results = []

    def record(condition: bool, name: str, details: str = "") -> None:
        results.append(check(condition, name, details))

    print("\nHealthcare Triage Agent — Automated Assessment Tests")
    print("Base URL:", base_url)
    print("=" * 62)

    # 1. Normal headache path, invalid yes/no, duration, and severity values.
    try:
        sid, pid = start_session(base_url)
        r = send(base_url, sid, "I have had a headache since yesterday.")
        record(r.get("state") == "awaiting_age", "Start session and identify headache",
               f"state={r.get('state')}")

        r = send(base_url, sid, "21")
        record("worst headache" in r.get("message", "").lower(),
               "Accept valid age and ask first headache question", r.get("message", ""))

        r = send(base_url, sid, "Maybe")
        record((not r.get("done")) and "yes or no" in r.get("message", "").lower(),
               "Reject invalid yes/no answer", r.get("message", ""))

        r = send(base_url, sid, "No")
        record("vision" in r.get("message", "").lower() or "weakness" in r.get("message", "").lower(),
               "Accept No and advance to neurological symptom question", r.get("message", ""))

        r = send(base_url, sid, "No")
        record("hours" in r.get("message", "").lower(),
               "Advance to headache duration question", r.get("message", ""))

        r = send(base_url, sid, "hello")
        record((not r.get("done")) and "valid number" in r.get("message", "").lower(),
               "Reject non-numeric duration", r.get("message", ""))

        r = send(base_url, sid, "-5")
        record((not r.get("done")) and "greater than or equal to zero" in r.get("message", "").lower(),
               "Reject negative duration", r.get("message", ""))

        r = send(base_url, sid, "24")
        record("1-10" in r.get("message", "").lower() or "scale" in r.get("message", "").lower(),
               "Accept duration and ask severity", r.get("message", ""))

        r = send(base_url, sid, "0")
        record((not r.get("done")) and "severity between 1 and 10" in r.get("message", "").lower(),
               "Reject severity below range", r.get("message", ""))

        r = send(base_url, sid, "11")
        record((not r.get("done")) and "severity between 1 and 10" in r.get("message", "").lower(),
               "Reject severity above range", r.get("message", ""))

        r = send(base_url, sid, "high")
        record((not r.get("done")) and "valid number" in r.get("message", "").lower(),
               "Reject non-numeric severity", r.get("message", ""))

        final = send(base_url, sid, "5")
        record(final.get("done") is True and final.get("state") == "done",
               "Complete normal headache assessment", f"state={final.get('state')}; urgency={final.get('urgency')}")
        record(final.get("urgency") == "low", "Normal headache case receives low urgency",
               f"urgency={final.get('urgency')}")
        record(not final.get("red_flags"), "Normal headache case has no red flags",
               f"red_flags={final.get('red_flags')}")

        # Doctor dashboard and final chat-history persistence.
        _, detail = request_json(base_url, "GET", f"/api/dashboard/sessions/{sid}")
        history = detail.get("chat_history", []) if isinstance(detail, dict) else []
        last_assistant = next((m.get("text", "") for m in reversed(history)
                               if m.get("role") == "assistant"), "")
        record(bool(history) and bool(last_assistant),
               "Dashboard record contains conversation history",
               f"messages={len(history)}")
        record(bool(final.get("message", "")) and final.get("message", "") in last_assistant,
               "Dashboard history includes final assistant response",
               f"last assistant message={last_assistant[:120]}")

        _, sessions = request_json(base_url, "GET", "/api/dashboard/sessions")
        ids = [item.get("id") for item in sessions] if isinstance(sessions, list) else []
        record(sid in ids, "Completed assessment appears in doctor dashboard list", f"session_id={sid}")

        _, timeline = request_json(base_url, "GET", f"/api/dashboard/timeline/{pid}")
        timeline_items = timeline.get("timeline", []) if isinstance(timeline, dict) else []
        record(any(item.get("session_id") == sid for item in timeline_items),
               "Completed assessment appears in patient timeline", f"patient_id={pid}")

    except Exception as exc:
        record(False, "Normal assessment and dashboard test sequence", str(exc))

    # 2. Emergency red-flag route.
    try:
        sid, _ = start_session(base_url)
        send(base_url, sid, "I have had a headache since yesterday.")
        send(base_url, sid, "21")
        emergency = send(base_url, sid, "Yes")
        record(emergency.get("done") is True, "Emergency red-flag answer finalizes assessment",
               f"state={emergency.get('state')}")
        record(emergency.get("urgency") == "emergency", "Emergency red flag produces emergency urgency",
               f"urgency={emergency.get('urgency')}")
        record(bool(emergency.get("red_flags")), "Emergency case records a red flag",
               f"red_flags={emergency.get('red_flags')}")
        record(emergency.get("escalate") is True, "Emergency case is escalated",
               f"escalate={emergency.get('escalate')}")
    except Exception as exc:
        record(False, "Emergency red-flag test sequence", str(exc))

    # 3. Invalid age handling.
    try:
        sid, _ = start_session(base_url)
        send(base_url, sid, "I have had a headache since yesterday.")
        r = send(base_url, sid, "hello")
        record((not r.get("done")) and "age" in r.get("message", "").lower(),
               "Reject non-numeric age", r.get("message", ""))
        r = send(base_url, sid, "-5")
        record((not r.get("done")) and "age" in r.get("message", "").lower(),
               "Reject negative age", r.get("message", ""))
        r = send(base_url, sid, "150")
        record((not r.get("done")) and "between 0 and 120" in r.get("message", "").lower(),
               "Reject age above 120", r.get("message", ""))
        r = send(base_url, sid, "21")
        record("worst headache" in r.get("message", "").lower(),
               "Accept valid age after invalid attempts", r.get("message", ""))
    except Exception as exc:
        record(False, "Age validation test sequence", str(exc))

    # Report.
    print()
    passed = sum(1 for ok, _, _ in results if ok)
    failed = len(results) - passed
    for ok, name, details in results:
        label = "PASS" if ok else "FAIL"
        print(f"[{label}] {name}")
        if details and not ok:
            print("       ", details.replace("\n", " "))
    print("-" * 62)
    print(f"RESULT: {passed} passed, {failed} failed, {len(results)} total")
    print("Note: These are simulated software tests, not clinical validation.")
    return 0 if failed == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Healthcare Triage Agent API tests")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000",
                        help="FastAPI server base URL (default: http://127.0.0.1:8000)")
    args = parser.parse_args()
    sys.exit(run_tests(args.base_url))


if __name__ == "__main__":
    main()
