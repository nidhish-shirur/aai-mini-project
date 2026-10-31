
const API = "/api";

let sessionId = null;
let patientId = localStorage.getItem("triage_patient_id") || null;
let done = false;

const messagesEl = document.getElementById("messages");
const textInput = document.getElementById("textInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const langSelect = document.getElementById("lang");
const newSessionBtn = document.getElementById("newSessionBtn");
const patientIdLabel = document.getElementById("patientIdLabel");

// Create New Patient button
const newPatientBtn = document.createElement("button");

newPatientBtn.id = "newPatientBtn";
newPatientBtn.textContent = "＋ New Patient";
newPatientBtn.style.cssText = `
    margin-left: 10px;
    padding: 8px 14px;
    border: none;
    border-radius: 6px;
    background: #2563eb;
    color: white;
    cursor: pointer;
`;

patientIdLabel.insertAdjacentElement("afterend", newPatientBtn);

// Start a completely new patient session
newPatientBtn.addEventListener("click", () => {
    const confirmed = confirm(
        "Start a new patient record? The current patient ID will be replaced."
    );

    if (!confirmed) return;

    patientId = null;
    localStorage.removeItem("triage_patient_id");

    startSession();
});

function addMessage(role, text) {
    const div = document.createElement("div");
    div.className = "msg " + role;
    div.textContent = text;

    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function urgencyBadgeHtml(urgency) {
    const labels = {
        emergency: "EMERGENCY",
        urgent: "URGENT",
        moderate: "MODERATE",
        low: "LOW"
    };

    return `<span class="badge ${urgency}">${labels[urgency] || urgency}</span>`;
}

async function renderResultCard(data) {
    const card = document.createElement("div");
    card.className = "result-card";

    let html = urgencyBadgeHtml(data.urgency);

    html += `<div><b>Care pathway:</b> ${data.care_pathway}</div>`;

    if (data.red_flags && data.red_flags.length) {
        html += `
            <div style="margin-top:6px;">
                <b>Flags noted:</b> ${data.red_flags.join("; ")}
            </div>
        `;
    }

    if (data.escalate) {
        html += `
            <div style="margin-top:6px;color:#dc2626;">
                <b>⚑ Flagged for clinician review</b>
            </div>
        `;
    }

    html += `
        <div id="hospitalList" style="margin-top:10px;">
            <b>Nearby / recommended care options:</b>
        </div>
    `;

    card.innerHTML = html;

    messagesEl.appendChild(card);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    // Retrieve hospital options from the original dummy directory.
    try {
        const res = await fetch(
            `${API}/hospitals?urgency=${data.urgency}`
        );

        const hd = await res.json();

        const list = card.querySelector("#hospitalList");

        hd.options.forEach(h => {
            const item = document.createElement("div");
            item.className = "hospital-item";

            item.innerHTML = `
                <b>${h.name}</b>
                <br>
                <span style="color:#64748b;">
                    ${h.distance_km} km away · ${h.phone}
                </span>
            `;

            list.appendChild(item);
        });

    } catch (e) {
        console.error("Hospital loading failed:", e);
    }
}

async function startSession() {
    messagesEl.innerHTML = "";
    done = false;

    textInput.disabled = false;
    sendBtn.disabled = false;

    const lang = langSelect.value;

    const res = await fetch(`${API}/session/start`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            patient_id: patientId,
            language: lang
        })
    });

    const data = await res.json();

    sessionId = data.session_id;
    patientId = data.patient_id;

    localStorage.setItem("triage_patient_id", patientId);

    patientIdLabel.textContent = `Patient ID: ${patientId}`;

    addMessage("assistant", data.message);
}

async function sendMessage() {
    const text = textInput.value.trim();

    if (!text || done) return;

    addMessage("user", text);

    textInput.value = "";
    sendBtn.disabled = true;

    const res = await fetch(
        `${API}/session/${sessionId}/message`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text })
        }
    );

    const data = await res.json();

    if (data.done) {
        done = true;

        addMessage(
            "assistant",
            data.message.split("\n\n")[0]
        );

        await renderResultCard(data);

        if (data.disclaimer) {
            const d = document.createElement("div");

            d.style.cssText =
                "font-size:11px;color:#94a3b8;text-align:center;margin-top:6px;";

            d.textContent = data.disclaimer;

            messagesEl.appendChild(d);
        }

        textInput.disabled = true;

    } else {
        addMessage("assistant", data.message);

        sendBtn.disabled = false;
        textInput.focus();
    }
}

// Send message using the button.
sendBtn.addEventListener("click", sendMessage);

// Send message by pressing Enter.
textInput.addEventListener("keydown", e => {
    if (e.key === "Enter") {
        sendMessage();
    }
});

// Start a new session.
newSessionBtn.addEventListener("click", startSession);

// Restart session when language changes.
langSelect.addEventListener("change", startSession);


// --------------------------------------------------
// Voice input (Advanced feature: Voice-Based Triage)
// Uses the browser's Web Speech API.
// --------------------------------------------------

let recognizing = false;
let recognition = null;

const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
        recognizing = true;

        micBtn.classList.add("listening");
        micBtn.title = "Listening... Click to stop";
    };

    recognition.onend = () => {
        recognizing = false;

        micBtn.classList.remove("listening");
        micBtn.title = "Click to speak";
    };

    recognition.onresult = event => {
        const transcript = event.results[0][0].transcript;

        // Put recognized speech in the input box.
        // The patient can review or edit it before sending.
        textInput.value = transcript;
        textInput.focus();
    };

    recognition.onerror = event => {
        recognizing = false;

        micBtn.classList.remove("listening");

        console.error(
            "Speech recognition error:",
            event.error
        );

        const errorMessages = {
            "not-allowed":
                "Microphone permission was denied. Please allow microphone access.",

            "no-speech":
                "No speech was detected. Please try again.",

            "audio-capture":
                "No microphone was detected.",

            "network":
                "Speech recognition network error. Please try again.",

            "service-not-allowed":
                "Speech recognition service is unavailable.",

            "language-not-supported":
                "The selected language is not supported."
        };

        addMessage(
            "assistant",
            errorMessages[event.error] ||
            "Voice input failed. Please try typing your response."
        );
    };

    micBtn.addEventListener("click", () => {
        if (recognizing) {
            recognition.stop();
            return;
        }

        recognition.lang =
            langSelect.value === "hi" ? "hi-IN" : "en-US";

        try {
            recognition.start();

        } catch (error) {
            console.error(
                "Could not start speech recognition:",
                error
            );

            addMessage(
                "assistant",
                "Could not start voice input. Please try again."
            );
        }
    });

} else {
    micBtn.title = "Voice input is not supported in this browser";
    micBtn.disabled = true;
    micBtn.style.opacity = "0.4";
}


// Start the application.
startSession();
