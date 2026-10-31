
"""Agent 2: Adaptive Questioning Agent
Handles adaptive question trees with strict input validation.
"""

import re
from knowledge_base import QUESTION_TREES


class AdaptiveQuestioningAgent:

    YES_WORDS = {
        "yes", "y", "yeah", "yep", "haan", "ha",
        "sure", "true",
        "हाँ", "हां", "जी हाँ", "जी हां",
        "बिल्कुल", "सही"
    }

    NO_WORDS = {
        "no", "n", "nope", "nahi", "na", "false",
        "नहीं", "नही", "जी नहीं", "जी नही",
        "बिल्कुल नहीं"
    }

    def first_question(self, symptom: str):
        tree = QUESTION_TREES.get(
            symptom, QUESTION_TREES["generic"]
        )
        start_qid = tree["start"]
        return start_qid, tree[start_qid]

    def normalize_yesno(self, text: str):
        value = text.strip().lower()

        # Normalize whitespace and common punctuation.
        value = " ".join(value.split())
        value = value.strip(".,!?।")

        if value in self.YES_WORDS:
            return "yes"

        if value in self.NO_WORDS:
            return "no"

        return None

    def parse_number(self, text: str, field: str):
        value = text.strip()

        # Accept only a valid numeric response.
        if not re.fullmatch(r"\d+(\.\d+)?", value):
            raise ValueError("Please enter a valid number.")

        number = float(value)

        if field == "severity":
            if not 1 <= number <= 10:
                raise ValueError(
                    "Severity must be between 1 and 10."
                )

        elif field in ("duration_days", "duration_hours",
                       "duration_minutes"):
            if number <= 0:
                raise ValueError(
                    "Duration must be greater than zero."
                )

        elif field == "temperature_f":
            if not 50 <= number <= 115:
                raise ValueError(
                    "Please enter a valid temperature in Fahrenheit."
                )

        return number

    def next_question(self, symptom: str, current_qid: str, answer_text: str):
        """Returns (next_qid_or_None, next_node_or_None, stored_value)."""
        tree = QUESTION_TREES.get(symptom, QUESTION_TREES["generic"])
        node = tree[current_qid]
        qtype = node["type"]

        if qtype == "yesno":
            norm = self.normalize_yesno(answer_text)

            if norm not in ("yes", "no"):
                raise ValueError("Please answer Yes or No.")

            stored_value = norm
            next_qid = node["next"].get(norm, node["next"].get("no"))

        elif qtype == "number":
            try:
                stored_value = float(answer_text.strip())
            except (ValueError, AttributeError):
                raise ValueError("Please enter a valid number.")

            if stored_value < 0:
                raise ValueError("Please enter a number greater than or equal to zero.")

            if node["field"] == "severity" and not 1 <= stored_value <= 10:
                raise ValueError("Please enter a severity between 1 and 10.")

            next_qid = node["next"].get("*")

        else:
            stored_value = answer_text.strip()

            if not stored_value:
                raise ValueError("Please provide an answer.")

            next_qid = node["next"].get("*")

        if next_qid is None:
            return None, None, stored_value

        return next_qid, tree[next_qid], stored_value