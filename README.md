# Healthcare Triage Agent (PS-07)

A multi-agent conversational triage assistant that collects symptoms, asks
adaptive follow-up questions, detects red flags, assesses urgency, recommends
a care pathway, and generates a structured clinical summary — **without ever
diagnosing**. Includes a doctor dashboard, population analytics, hospital
routing, symptom timelines, voice input, and English/Hindi support.

⚠️ **This is a hackathon/demo build using rule-based clinical triage logic
modeled loosely on common triage heuristics. It is NOT validated for real
clinical use and must not be deployed to real patients without proper
clinical review, regulatory approval, and testing.**

## Quick start

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open:
- **http://localhost:8000/** — patient chat interface
- **http://localhost:8000/dashboard** — doctor dashboard
- **http://localhost:8000/docs** — interactive API docs (Swagger)

No API keys or external services required — everything runs locally.

## Architecture — 11 agents, as specified

| # | Agent | File | Role |
|---|-------|------|------|
| 1 | Symptom Collection Agent | `agents/symptom_collection.py` | Extracts chief-complaint category from free text |
| 2 | Adaptive Questioning Agent | `agents/adaptive_questioning.py` | Walks a branching per-symptom decision tree |
| 3 | Medical Knowledge Agent | `agents/medical_knowledge.py` | Rule-based clinical signal detection (e.g. chest pain + sweating) |
| 4 | Risk Assessment Agent | `agents/risk_assessment.py` | Aggregates signals into an urgency tier |
| 5 | Red Flag Detection Agent | `agents/red_flag_detection.py` | Immediate-escalation dangerous symptom detection |
| 6 | Care Pathway Agent | `agents/care_pathway.py` | Maps urgency → ED / Urgent Care / Primary Care / Self-care |
| 7 | Medical Summary Agent | `agents/medical_summary.py` | Structured, doctor-readable summary |
| 8 | Conversation Memory Agent | `agents/conversation_memory.py` | Session + cross-session (patient) memory |
| 9 | Safety & Compliance Agent | `agents/safety_compliance.py` | Strips any diagnostic-sounding language from output |
| 10 | Escalation Agent | `agents/escalation.py` | Decides if a human clinician must review the case |
| 11 | Master Orchestrator | `agents/orchestrator.py` | Coordinates all agents turn-by-turn |

Clinical rules (symptom trees, red-flag triggers, urgency scoring, care
pathways, translations, mock hospital directory) all live in one place:
`backend/knowledge_base.py` — easy to extend or hand to a real clinician for
review.

## Advanced features implemented

- **Symptom Timeline Builder** — `/api/dashboard/timeline/{patient_id}` aggregates a patient's symptoms across multiple sessions/days (pass the same `patient_id` across chats to see it build).
- **Multilingual Triage** — English + Hindi, toggle in the chat UI; all question trees and care-pathway text are translated.
- **Voice-Based Triage** — real browser Web Speech API integration (mic button in chat UI); speaks → transcribes → auto-sends.
- **Doctor Dashboard** — `/dashboard`: session table, click-through structured summary, red flags, escalation reasons, and that patient's timeline.
- **Hospital Routing** — `/api/hospitals?urgency=X` returns a mock nearest-care directory filtered by urgency tier, shown after every triage result.
- **Population Health Analytics** — `/api/analytics/population`: case counts by symptom and urgency, escalation rate, shown at the top of the dashboard.

## Data model / storage

Uses in-memory storage (`backend/storage.py`) for the demo — zero setup
required. It's isolated behind clean functions (`create_session`,
`finalize_session`, `patient_timeline`, `population_stats`, ...), so swapping
in Postgres/Mongo later means only touching `storage.py`, not any agent.

## Where an LLM would slot in (not included, by design)

The symptom-extraction step (`symptom_collection.py`) currently uses keyword
matching, which is transparent, safe, and needs no API key. For messier
free text ("I feel like something's off with my stomach since Tuesday"),
you could swap that one function for an LLM call to classify into the same
fixed symptom categories — the rest of the pipeline (red flags, trees,
scoring, safety filter) stays deterministic and rule-based on purpose, since
that's what makes it auditable and safe for a medical triage context.

## Testing it yourself

Try these in the chat to see different paths:
- `"I have chest pain"` → age → "does it spread to your arm" → yes → "sweating?" → yes → **Emergency, escalated**
- `"I have had a fever for three days"` → mirrors the exact example in the spec
- `"my friend just passed out"` → immediate emergency, no further questions asked
- Anything not in the keyword list → falls into the generic tree and is auto-escalated for clinician review (safety-first default for unmatched symptoms)

## Project structure

```
healthcare-triage-agent/
├── backend/
│   ├── main.py                 # FastAPI app & all routes
│   ├── models.py                # Request/response schemas
│   ├── storage.py               # In-memory session/dashboard/timeline store
│   ├── knowledge_base.py        # All clinical rules, trees, translations
│   ├── requirements.txt
│   └── agents/                  # 11 agents, one file each
├── frontend/
│   ├── index.html / app.js      # Patient chat (+ voice input)
│   ├── dashboard.html / dashboard.js  # Doctor dashboard
│   └── style.css
└── README.md
```
