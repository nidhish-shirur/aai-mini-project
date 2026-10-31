
"""Agent 1: Symptom Collection Agent

Uses keyword matching first and Groq as a fallback
to understand free-text symptom descriptions.
"""

import json
import os

from dotenv import load_dotenv
from groq import Groq

from knowledge_base import SYMPTOM_KEYWORDS


load_dotenv()

SUPPORTED_SYMPTOMS = set(SYMPTOM_KEYWORDS.keys())

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


class SymptomCollectionAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        self.client = Groq(api_key=api_key) if api_key else None

    def extract_symptom(self, raw_text: str) -> str:
        """Identify a symptom using keywords first, then Groq."""

        text = raw_text.lower().strip()

        # Step 1: Try existing keyword-based recognition.
        for symptom, keywords in SYMPTOM_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return symptom

        # Step 2: Use Groq only if keyword matching fails.
        if self.client is None:
            return "generic"

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a symptom classification component "
                            "in a healthcare triage application. "
                            "Identify the main symptom category from the "
                            "patient's description. Do not diagnose, "
                            "recommend treatment, or assess urgency. "
                            "Return only valid JSON in this format: "
                            '{"symptom": "category"}. '
                            "Allowed categories: "
                            + ", ".join(sorted(SUPPORTED_SYMPTOMS))
                            + ", generic. "
                            "If the description is unclear or does not "
                            "match a category, return generic. "
                            "Do not explain your reasoning. "
                            "Return the JSON answer immediately."
                        ),
                    },
                    {
                        "role": "user",
                        "content": raw_text,
                    },
                ],
                temperature=0,
                max_completion_tokens=500,
            )

            result = response.choices[0].message.content

            if not result:
                return "generic"

            # Extract and validate the JSON response.
            result = result.strip()
            result = result.replace("```json", "").replace("```", "").strip()

            data = json.loads(result)
            symptom = str(data.get("symptom", "generic")).strip().lower()

            if symptom in SUPPORTED_SYMPTOMS:
                return symptom

            return "generic"

        except Exception as error:
            print("Groq symptom recognition failed:", error)
            return "generic"
