const API = "/api";

function badge(urgency) {
  const labels = { emergency: "EMERGENCY", urgent: "URGENT", moderate: "MODERATE", low: "LOW" };
  return `<span class="badge ${urgency}">${labels[urgency] || urgency}</span>`;
}

async function loadStats() {
  const res = await fetch(`${API}/analytics/population`);
  const d = await res.json();
  const statsEl = document.getElementById("stats");
  const topSymptom = Object.entries(d.by_symptom)[0];
  statsEl.innerHTML = `
    <div class="stat-card"><div class="value">${d.total_cases}</div><div class="label">Total cases</div></div>
    <div class="stat-card"><div class="value">${d.by_urgency.emergency || 0}</div><div class="label">Emergency cases</div></div>
    <div class="stat-card"><div class="value">${d.escalated_count}</div><div class="label">Escalated to clinician</div></div>
    <div class="stat-card"><div class="value">${topSymptom ? topSymptom[0].replace('_',' ') : '—'}</div><div class="label">Most common complaint</div></div>
  `;
}

async function loadSessions() {
  const res = await fetch(`${API}/dashboard/sessions`);
  const rows = await res.json();
  const tbody = document.getElementById("sessionRows");
  tbody.innerHTML = "";
  rows.forEach(r => {
    const tr = document.createElement("tr");
    const time = new Date(r.created_at).toLocaleString();
    tr.innerHTML = `
      <td>${time}</td>
      <td>${r.patient_id}</td>
      <td>${r.age ?? "—"}</td>
      <td>${(r.symptom || "").replace("_", " ")}</td>
      <td>${badge(r.urgency)}</td>
      <td>${r.escalate ? "⚑ Yes" : "No"}</td>
    `;
    tr.addEventListener("click", () => showDetail(r));
    tbody.appendChild(tr);
  });
  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#94a3b8;padding:24px;">No sessions yet. Complete a chat on the patient side first.</td></tr>`;
  }
}

async function showDetail(record) {
  const panel = document.getElementById("detailPanel");
  panel.style.display = "block";

  const timelineRes = await fetch(`${API}/dashboard/timeline/${record.patient_id}`);
  const timelineData = await timelineRes.json();
  const timelineHtml = timelineData.timeline.map(t =>
    `<li>${t.date}: <b>${(t.symptom||'').replace('_',' ')}</b> — ${badge(t.urgency)}</li>`
  ).join("");

  const answersHtml = Object.entries(record.answers || {}).map(([k, v]) =>
    `<div class="kv"><b>${k.replace(/_/g, ' ')}</b><span>${v}</span></div>`
  ).join("");

  panel.innerHTML = `
    <h3>Structured Summary — ${record.patient_id} <small style="color:#94a3b8;">(${record.id})</small></h3>
    <div class="kv"><b>Age</b><span>${record.age ?? "—"}</span></div>
    <div class="kv"><b>Chief complaint</b><span>${(record.symptom||"").replace("_"," ")}</span></div>
    <div class="kv"><b>Urgency</b><span>${badge(record.urgency)}</span></div>
    <div class="kv"><b>Care pathway</b><span>${record.care_pathway}</span></div>
    <div class="kv"><b>Red flags</b><span>${(record.red_flags && record.red_flags.length) ? record.red_flags.join("; ") : "None"}</span></div>
    <div class="kv"><b>Escalated?</b><span>${record.escalate ? "Yes — " + (record.escalate_reasons||[]).join("; ") : "No"}</span></div>
    <h4 style="margin-top:16px;">Collected Answers</h4>
    ${answersHtml || "<div style='color:#94a3b8;'>None</div>"}
    <h4 style="margin-top:16px;">Symptom Timeline — this patient</h4>
    <ul>${timelineHtml || "<li style='color:#94a3b8;'>No prior sessions</li>"}</ul>
  `;
  panel.scrollIntoView({ behavior: "smooth" });
}

loadStats();
loadSessions();
setInterval(() => { loadStats(); loadSessions(); }, 8000);
