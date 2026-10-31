"""
knowledge_base.py
Central clinical/triage knowledge base used by all agents.
This is a RULE-BASED protocol layer (not an LLM, not a diagnostic engine).
Every rule here maps symptoms/answers -> urgency signals and care pathways,
modeled loosely on common ER/urgent-care triage heuristics (e.g. simplified
Manchester Triage / ESI style logic). This is a hackathon-grade demo and is
NOT validated for real clinical use.
"""

from datetime import datetime

DISCLAIMER = (
    "This is not a medical diagnosis. It is a triage guide to help you find the "
    "right level of care. If you believe this is a medical emergency, call your "
    "local emergency number immediately."
)

EMERGENCY_NUMBER = {"en": "112 (India) / your local emergency number", "hi": "112 (भारत) / अपनी स्थानीय आपातकालीन सेवा"}

# ---------------------------------------------------------------------------
# 1. SYMPTOM KEYWORD MAP  (used by SymptomCollectionAgent)
# ---------------------------------------------------------------------------
SYMPTOM_KEYWORDS = {
    "chest_pain": [
        "chest pain", "chest hurts", "pain in my chest",
        "tightness in chest", "chest pressure",
        "सीने में दर्द", "छाती में दर्द", "सीने में तकलीफ"
    ],

    "breathing_difficulty": [
        "can't breathe", "cant breathe", "difficulty breathing",
        "shortness of breath", "breathless", "trouble breathing",
        "gasping", "सांस लेने में कठिनाई", "सांस नहीं आ रही",
        "सांस फूलना", "सांस लेने में परेशानी"
    ],

    "fever": [
        "fever", "temperature", "feverish", "hot and cold", "chills",
        "बुखार", "तेज बुखार", "तापमान"
    ],

    "abdominal_pain": [
        "stomach pain", "abdominal pain", "belly pain",
        "stomach ache", "tummy pain", "stomach hurts",
        "पेट दर्द", "पेट में दर्द", "पेट में तकलीफ"
    ],

    "headache": [
        "headache", "head pain", "migraine", "head hurts",
        "सिरदर्द", "सिर दर्द", "सिर में दर्द", "माइग्रेन"
    ],

    "cough": [
        "cough", "coughing", "खांसी", "खाँसी"
    ],

    "bleeding": [
        "bleeding", "blood loss", "cut deeply",
        "hemorrhage", "won't stop bleeding",
        "खून बहना", "रक्तस्राव", "खून निकलना"
    ],

    "loss_of_consciousness": [
        "fainted", "passed out", "unconscious",
        "blacked out", "collapsed",
        "बेहोश", "बेहोशी", "होश खोना"
    ],

    "stroke_symptoms": [
        "face drooping", "slurred speech", "arm weakness",
        "one side numb", "face is drooping",
        "चेहरा टेढ़ा होना", "बोलने में कठिनाई",
        "शरीर के एक तरफ कमजोरी", "एक तरफ सुन्नपन"
    ],

    "injury": [
        "fell down", "broke my", "fracture",
        "sprained", "injury", "hit my head",
        "चोट लगना", "गिर जाना", "हड्डी टूटना",
        "मोच आना"
    ],
}

# Symptoms that are ALWAYS an immediate red flag the instant they're mentioned,
# no matter what tree state we're in.
IMMEDIATE_RED_FLAG_SYMPTOMS = {
    "chest_pain": "Reported chest pain — requires immediate medical evaluation",
    "breathing_difficulty": "Reported difficulty breathing — requires immediate medical evaluation",
    "loss_of_consciousness": "Reported loss of consciousness / fainting episode",
    "stroke_symptoms": "Reported possible stroke signs (facial drooping, slurred speech, one-sided weakness)",
}

# ---------------------------------------------------------------------------
# 2. QUESTION TREES  (used by AdaptiveQuestioningAgent)
# Each tree: {"start": <qid>, <qid>: {field, type, text{en,hi}, next{...}}}
# type: "yesno" | "number" | "text"
# next for yesno: {"yes": qid|None, "no": qid|None}
# next for number/text: {"*": qid|None}
# ---------------------------------------------------------------------------
QUESTION_TREES = {
    "chest_pain": {
        "start": "radiates",
        "radiates": {"field": "radiates_arm", "type": "yesno",
            "text": {"en": "Does the pain spread to your arm, jaw, or back?",
                      "hi": "क्या दर्द आपकी बांह, जबड़े या पीठ तक फैलता है?"},
            "next": {"yes": "sweating", "no": "breath_pain"}},
        "sweating": {"field": "sweating_nausea", "type": "yesno",
            "text": {"en": "Are you sweating heavily or feeling nauseous right now?",
                      "hi": "क्या आपको अभी बहुत पसीना आ रहा है या जी मिचला रहा है?"},
            "next": {"yes": "duration", "no": "duration"}},
        "breath_pain": {"field": "worse_on_breathing", "type": "yesno",
            "text": {"en": "Does the pain get worse when you breathe deeply?",
                      "hi": "क्या गहरी सांस लेने पर दर्द बढ़ जाता है?"},
            "next": {"yes": "duration", "no": "duration"}},
        "duration": {"field": "duration_minutes", "type": "number",
            "text": {"en": "How many minutes/hours has this pain lasted? (enter a number of minutes)",
                      "hi": "यह दर्द कितनी देर से है? (मिनटों में संख्या दर्ज करें)"},
            "next": {"*": "severity"}},
        "severity": {"field": "severity", "type": "number",
            "text": {"en": "On a scale of 1-10, how severe is the pain?",
                      "hi": "1 से 10 के पैमाने पर दर्द कितना गंभीर है?"},
            "next": {"*": None}},
    },
    "fever": {
        "start": "temperature",
        "temperature": {"field": "temperature_f", "type": "number",
            "text": {"en": "What is your temperature in Fahrenheit? (e.g. 101)",
                      "hi": "आपका तापमान फ़ारेनहाइट में क्या है? (जैसे 101)"},
            "next": {"*": "duration"}},
        "duration": {"field": "duration_days", "type": "number",
            "text": {"en": "How many days have you had this fever?",
                      "hi": "आपको यह बुखार कितने दिनों से है?"},
            "next": {"*": "breathing"}},
        "breathing": {"field": "breathing_difficulty", "type": "yesno",
            "text": {"en": "Any difficulty breathing?", "hi": "क्या सांस लेने में कोई कठिनाई है?"},
            "next": {"yes": "chest_pain", "no": "chest_pain"}},
        "chest_pain": {"field": "chest_pain", "type": "yesno",
            "text": {"en": "Any chest pain?", "hi": "क्या सीने में दर्द है?"},
            "next": {"yes": "travel", "no": "travel"}},
        "travel": {"field": "recent_travel", "type": "yesno",
            "text": {"en": "Any recent travel in the last 2 weeks?", "hi": "क्या पिछले 2 हफ्तों में कोई यात्रा की है?"},
            "next": {"yes": "conditions", "no": "conditions"}},
        "conditions": {"field": "existing_conditions", "type": "yesno",
            "text": {"en": "Any existing medical conditions (diabetes, heart disease, etc.)?",
                      "hi": "क्या आपको कोई मौजूदा बीमारी है (जैसे मधुमेह, हृदय रोग)?"},
            "next": {"*": None}},
    },
    "abdominal_pain": {
        "start": "location",
        "location": {"field": "location", "type": "text",
            "text": {"en": "Where is the pain located? (upper/lower/left/right/general)",
                      "hi": "दर्द कहाँ है? (ऊपर/नीचे/बाएं/दाएं/सामान्य)"},
            "next": {"*": "duration"}},
        "duration": {"field": "duration_days", "type": "number",
            "text": {"en": "How many days has this pain lasted?", "hi": "यह दर्द कितने दिनों से है?"},
            "next": {"*": "severity"}},
        "severity": {"field": "severity", "type": "number",
            "text": {"en": "On a scale of 1-10, how severe is the pain?", "hi": "दर्द 1 से 10 के पैमाने पर कितना गंभीर है?"},
            "next": {"*": "vomiting"}},
        "vomiting": {"field": "vomiting", "type": "yesno",
            "text": {"en": "Any vomiting?", "hi": "क्या उल्टी हो रही है?"},
            "next": {"yes": "fever", "no": "fever"}},
        "fever": {"field": "fever", "type": "yesno",
            "text": {"en": "Any fever along with this?", "hi": "क्या इसके साथ बुखार भी है?"},
            "next": {"*": None}},
    },
    "headache": {
        "start": "sudden_onset",
        "sudden_onset": {"field": "sudden_onset", "type": "yesno",
            "text": {"en": "Is this the sudden 'worst headache of your life', unlike any before?",
                      "hi": "क्या यह अचानक हुआ, आपके जीवन का 'सबसे भीषण सिरदर्द' है?"},
            "next": {"yes": "vision", "no": "vision"}},
        "vision": {"field": "vision_changes", "type": "yesno",
            "text": {"en": "Any vision changes, confusion, or weakness on one side?",
                      "hi": "क्या दृष्टि में बदलाव, भ्रम, या शरीर के एक तरफ कमजोरी है?"},
            "next": {"yes": "duration", "no": "duration"}},
        "duration": {"field": "duration_hours", "type": "number",
            "text": {"en": "How many hours has this headache lasted?", "hi": "यह सिरदर्द कितने घंटों से है?"},
            "next": {"*": "severity"}},
        "severity": {"field": "severity", "type": "number",
            "text": {"en": "On a scale of 1-10, how severe is it?", "hi": "यह 1 से 10 के पैमाने पर कितना गंभीर है?"},
            "next": {"*": None}},
    },
    "breathing_difficulty": {
        "start": "sudden_onset",
        "sudden_onset": {"field": "sudden_onset", "type": "yesno",
            "text": {"en": "Did this start suddenly?", "hi": "क्या यह अचानक शुरू हुआ?"},
            "next": {"*": "chest_pain"}},
        "chest_pain": {"field": "chest_pain", "type": "yesno",
            "text": {"en": "Any chest pain along with it?", "hi": "क्या इसके साथ सीने में दर्द भी है?"},
            "next": {"*": "lips_bluish"}},
        "lips_bluish": {"field": "lips_bluish", "type": "yesno",
            "text": {"en": "Are your lips or face turning bluish/grey?", "hi": "क्या आपके होंठ या चेहरा नीला/धूसर हो रहा है?"},
            "next": {"yes": "duration", "no": "duration"}},
        "duration": {"field": "duration_minutes", "type": "number",
            "text": {"en": "How many minutes has this lasted?", "hi": "यह कितने मिनटों से है?"},
            "next": {"*": None}},
    },
    "cough": {
        "start": "duration",
        "duration": {"field": "duration_days", "type": "number",
            "text": {"en": "How many days have you had this cough?", "hi": "यह खांसी कितने दिनों से है?"},
            "next": {"*": "blood"}},
        "blood": {"field": "blood_in_cough", "type": "yesno",
            "text": {"en": "Any blood in your cough?", "hi": "क्या खांसी में खून आ रहा है?"},
            "next": {"yes": "fever", "no": "fever"}},
        "fever": {"field": "fever", "type": "yesno",
            "text": {"en": "Any fever with the cough?", "hi": "क्या खांसी के साथ बुखार भी है?"},
            "next": {"*": "breathing"}},
        "breathing": {"field": "breathing_difficulty", "type": "yesno",
            "text": {"en": "Any difficulty breathing?", "hi": "क्या सांस लेने में कठिनाई है?"},
            "next": {"*": None}},
    },
    "bleeding": {
        "start": "can_stop",
        "can_stop": {"field": "can_stop_bleeding", "type": "yesno",
            "text": {"en": "Are you able to stop or slow the bleeding with direct pressure?",
                      "hi": "क्या आप सीधा दबाव डालकर रक्तस्राव को रोक या धीमा कर पा रहे हैं?"},
            "next": {"*": "amount"}},
        "amount": {"field": "amount", "type": "text",
            "text": {"en": "How much bleeding — small, moderate, or large amount?",
                      "hi": "कितना रक्तस्राव है - कम, मध्यम, या अधिक?"},
            "next": {"*": None}},
    },
    "injury": {
        "start": "location",
        "location": {"field": "location", "type": "text",
            "text": {"en": "Which part of the body is injured?", "hi": "शरीर का कौन सा हिस्सा घायल है?"},
            "next": {"*": "can_move"}},
        "can_move": {"field": "can_move", "type": "yesno",
            "text": {"en": "Can you move/use that part normally?", "hi": "क्या आप उस हिस्से को सामान्य रूप से हिला/इस्तेमाल कर सकते हैं?"},
            "next": {"*": "severity"}},
        "severity": {"field": "severity", "type": "number",
            "text": {"en": "On a scale of 1-10, how severe is the pain?", "hi": "दर्द 1 से 10 के पैमाने पर कितना गंभीर है?"},
            "next": {"*": None}},
    },
    "generic": {
        "start": "duration",
        "duration": {"field": "duration_days", "type": "text",
            "text": {"en": "How long have you had this symptom?", "hi": "आपको यह लक्षण कितने समय से है?"},
            "next": {"*": "severity"}},
        "severity": {"field": "severity", "type": "number",
            "text": {"en": "On a scale of 1-10, how severe is it?", "hi": "यह 1 से 10 के पैमाने पर कितना गंभीर है?"},
            "next": {"*": "associated"}},
        "associated": {"field": "associated_symptoms", "type": "text",
            "text": {"en": "Any other symptoms alongside this?", "hi": "क्या इसके साथ कोई अन्य लक्षण भी हैं?"},
            "next": {"*": "conditions"}},
        "conditions": {"field": "existing_conditions", "type": "yesno",
            "text": {"en": "Any existing medical conditions?", "hi": "क्या कोई मौजूदा बीमारी है?"},
            "next": {"*": None}},
    },
}

AGE_QUESTION = {"en": "First, how old are you (or the patient)?", "hi": "पहले बताएं, आपकी (या मरीज़ की) उम्र क्या है?"}

# ---------------------------------------------------------------------------
# 3. PER-ANSWER RED FLAG TRIGGERS (used by RedFlagDetectionAgent)
# ---------------------------------------------------------------------------
RED_FLAG_TRIGGERS = [
    {"symptom": "chest_pain", "field": "sweating_nausea", "value": "yes",
     "flag": "Chest pain with sweating/nausea — possible cardiac event"},
    {"symptom": "headache", "field": "sudden_onset", "value": "yes",
     "flag": "Sudden 'worst headache of life' — possible stroke/hemorrhage"},
    {"symptom": "headache", "field": "vision_changes", "value": "yes",
     "flag": "Headache with vision changes/weakness — possible neurological emergency"},
    {"symptom": "breathing_difficulty", "field": "lips_bluish", "value": "yes",
     "flag": "Bluish lips/face — possible severe hypoxia"},
    {"symptom": "cough", "field": "blood_in_cough", "value": "yes",
     "flag": "Coughing blood — needs urgent evaluation"},
    {"symptom": "bleeding", "field": "can_stop_bleeding", "value": "no",
     "flag": "Uncontrolled bleeding — medical emergency"},
]

# ---------------------------------------------------------------------------
# 4. CLINICAL SIGNAL RULES  (used by MedicalKnowledgeAgent)
# Boolean-field combos -> named signal + weight (0-100 scale contribution)
# ---------------------------------------------------------------------------
CLINICAL_SIGNAL_RULES = [
    {"symptom": "chest_pain", "conditions": {"radiates_arm": "yes", "sweating_nausea": "yes"},
     "signal": "possible_cardiac_event", "weight": 100},
    {"symptom": "chest_pain", "conditions": {"worse_on_breathing": "yes"},
     "signal": "pleuritic_chest_pain", "weight": 35},
    {"symptom": "fever", "conditions": {"breathing_difficulty": "yes"},
     "signal": "fever_with_respiratory_distress", "weight": 60},
    {"symptom": "fever", "conditions": {"existing_conditions": "yes"},
     "signal": "fever_with_comorbidity", "weight": 25},
    {"symptom": "abdominal_pain", "conditions": {"vomiting": "yes", "fever": "yes"},
     "signal": "abdominal_pain_with_vomiting_fever", "weight": 45},
    {"symptom": "breathing_difficulty", "conditions": {"sudden_onset": "yes", "chest_pain": "yes"},
     "signal": "acute_respiratory_event", "weight": 70},
    {"symptom": "cough", "conditions": {"breathing_difficulty": "yes", "fever": "yes"},
     "signal": "possible_respiratory_infection", "weight": 40},
    {"symptom": "injury", "conditions": {"can_move": "no"},
     "signal": "possible_fracture_or_serious_injury", "weight": 40},
]

# ---------------------------------------------------------------------------
# 5. CARE PATHWAYS  (used by CarePathwayAgent)
# ---------------------------------------------------------------------------
CARE_PATHWAY_MAP = {
    "emergency": {
        "en": "This looks like a medical emergency. Please call emergency services or go to the nearest Emergency Department right now.",
        "hi": "यह एक चिकित्सा आपातकाल जैसा लगता है। कृपया अभी आपातकालीन सेवाओं को कॉल करें या निकटतम आपातकालीन विभाग जाएं।",
    },
    "urgent": {
        "en": "Please visit an Emergency Department or Urgent Care center as soon as possible today.",
        "hi": "कृपया आज जल्द से जल्द आपातकालीन विभाग या अर्जेंट केयर सेंटर जाएं।",
    },
    "moderate": {
        "en": "Please schedule an appointment with a primary care doctor within the next 1-2 days.",
        "hi": "कृपया अगले 1-2 दिनों में एक प्राथमिक देखभाल चिकित्सक से अपॉइंटमेंट लें।",
    },
    "low": {
        "en": "Self-care and monitoring at home should be fine. See a doctor if symptoms worsen or don't improve in a few days.",
        "hi": "घर पर स्व-देखभाल और निगरानी पर्याप्त होनी चाहिए। यदि लक्षण बिगड़ें या कुछ दिनों में ठीक न हों तो डॉक्टर से मिलें।",
    },
}

URGENCY_LABEL_TRANSLATIONS = {
    "en": {
        "emergency": "Emergency",
        "urgent": "Urgent",
        "moderate": "Moderate",
        "low": "Low"
    },
    "hi": {
        "emergency": "आपातकालीन",
        "urgent": "तत्काल",
        "moderate": "मध्यम",
        "low": "कम"
    }
}

# ---------------------------------------------------------------------------
# 6. SAFETY & COMPLIANCE  (used by SafetyComplianceAgent)
# ---------------------------------------------------------------------------
BANNED_PATTERNS = [
    "you have ", "you might have ", "you probably have ", "you likely have ",
    "this is definitely ", "diagnosis:", "you are suffering from ", "it's probably ",
]
SAFE_REPLACEMENT = "Your symptoms warrant medical evaluation."

# ---------------------------------------------------------------------------
# 7. MOCK HOSPITAL / CARE DIRECTORY  (used by hospital routing feature)
# ---------------------------------------------------------------------------
HOSPITALS = [
    {"name": "City General Hospital — Emergency Dept", "type": "emergency", "distance_km": 2.1, "phone": "022-1234-5000"},
    {"name": "Metro Urgent Care Clinic", "type": "urgent", "distance_km": 1.4, "phone": "022-1234-5100"},
    {"name": "Sunrise Family Clinic (Primary Care)", "type": "moderate", "distance_km": 0.9, "phone": "022-1234-5200"},
    {"name": "TeleHealth Now — Video Consultation", "type": "low", "distance_km": 0.0, "phone": "app://teleconsult"},
]

def hospitals_for_urgency(urgency: str):
    if urgency == "emergency":
        return [h for h in HOSPITALS if h["type"] in ("emergency", "urgent")]
    if urgency == "urgent":
        return [h for h in HOSPITALS if h["type"] in ("urgent", "emergency")]
    if urgency == "moderate":
        return [h for h in HOSPITALS if h["type"] in ("moderate", "urgent")]
    return [h for h in HOSPITALS if h["type"] in ("low", "moderate")]

# ---------------------------------------------------------------------------
# 8. UI STRING TRANSLATIONS  (used by frontend + agents for fixed strings)
# ---------------------------------------------------------------------------
UI_STRINGS = {
    "greeting": {"en": "Hi, I'm a triage assistant. Please describe what's bothering you today.",
                  "hi": "नमस्ते, मैं एक ट्राइएज सहायक हूं। कृपया बताएं कि आज आपको क्या परेशानी है।"},
    "escalated": {"en": "Your case has been flagged for a human clinician's review.",
                   "hi": "आपके मामले को मानव चिकित्सक की समीक्षा के लिए चिह्नित किया गया है।"},
}
