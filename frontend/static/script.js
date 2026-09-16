const dropzone = document.getElementById("dropzone");
const resumeInput = document.getElementById("resume-input");
const folderInput = document.getElementById("folder-input");
const folderBtn = document.getElementById("folder-btn");
const dropzoneTitle = document.getElementById("dropzone-title");
const analyzeBtn = document.getElementById("analyze-btn");
const form = document.getElementById("analyze-form");
const statusLog = document.getElementById("status-log");
const errorBox = document.getElementById("error-box");
const mockNotice = document.getElementById("mock-notice");
const emptyState = document.getElementById("empty-state");
const results = document.getElementById("results");
const resultsCount = document.getElementById("results-count");
const tbody = document.getElementById("candidate-tbody");

const modalOverlay = document.getElementById("modal-overlay");
const modalLoading = document.getElementById("modal-loading");
const modalBody = document.getElementById("modal-body");
const modalClose = document.getElementById("modal-close");

let selectedFiles = [];
let jobList = [];
let candidates = {}; // candidate_id -> latest known data

const positionsList = document.getElementById("positions-list");
const addPositionToggle = document.getElementById("add-position-toggle");
const addPositionForm = document.getElementById("add-position-form");
const positionError = document.getElementById("position-error");

function renderPositions(jobsDetail) {
  positionsList.innerHTML = jobsDetail.map(j => `
    <div class="position-row">
      <strong>${j.title}</strong>
      <span>${j.skills.map(s => s.skill).join(", ")}</span>
    </div>
  `).join("");
}

function loadPositions() {
  fetch("/api/target-jobs")
    .then(r => r.json())
    .then(data => {
      jobList = data.jobs;
      renderPositions(data.jobs_detail || []);
      if (data.mock_mode) mockNotice.hidden = false;
    })
    .catch(() => {
      errorBox.hidden = false;
      errorBox.textContent = "Couldn't reach the server. Is app.py running?";
    });
}
loadPositions();

addPositionToggle.addEventListener("click", () => {
  addPositionForm.hidden = !addPositionForm.hidden;
});

addPositionForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  positionError.hidden = true;

  const title = document.getElementById("position-title").value.trim();
  const critical = document.getElementById("position-critical").value.split(",").map(s => s.trim()).filter(Boolean);
  const niceToHave = document.getElementById("position-nice").value.split(",").map(s => s.trim()).filter(Boolean);

  const resp = await fetch("/api/positions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, critical_skills: critical, nice_to_have_skills: niceToHave }),
  });
  const data = await resp.json();

  if (!resp.ok) {
    positionError.hidden = false;
    positionError.textContent = data.error;
    return;
  }

  addPositionForm.reset();
  addPositionForm.hidden = true;
  loadPositions();
});

// ---------- Dropzone ----------
dropzone.addEventListener("click", () => resumeInput.click());
dropzone.setAttribute("tabindex", "0");
dropzone.setAttribute("role", "button");
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); resumeInput.click(); }
});

["dragenter", "dragover"].forEach(evt =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); })
);
["dragleave", "drop"].forEach(evt =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("drag-over"); })
);
dropzone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) setFiles([...e.dataTransfer.files]);
});
resumeInput.addEventListener("change", () => {
  if (resumeInput.files.length) setFiles([...resumeInput.files]);
});

folderBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  folderInput.click();
});
folderInput.addEventListener("change", () => {
  // Folders can contain non-resume files (e.g. .DS_Store) - filter to
  // just the file types this app actually supports.
  const files = [...folderInput.files].filter(f =>
    f.name.toLowerCase().endsWith(".pdf") || f.name.toLowerCase().endsWith(".txt")
  );
  if (files.length) setFiles(files);
});

function setFiles(files) {
  selectedFiles = files;
  dropzone.classList.add("has-file");
  dropzoneTitle.textContent = files.length === 1 ? files[0].name : `${files.length} files selected`;
  analyzeBtn.disabled = false;
}

// ---------- Status log ----------
function showStatus(text) {
  statusLog.hidden = false;
  statusLog.innerHTML = `<div class="status-line active"><span class="status-dot"></span>${text}</div>`;
}
function hideStatus() { statusLog.hidden = true; }

// ---------- Submit bulk analysis ----------
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedFiles.length) return;

  errorBox.hidden = true;
  analyzeBtn.disabled = true;
  showStatus(`Parsing ${selectedFiles.length} resume${selectedFiles.length > 1 ? "s" : ""} and scoring candidates…`);

  const formData = new FormData();
  selectedFiles.forEach(f => formData.append("resumes", f));

  try {
    const resp = await fetch("/api/analyze-bulk", { method: "POST", body: formData });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Something went wrong.");

    hideStatus();
    if (data.errors && data.errors.length) {
      errorBox.hidden = false;
      errorBox.textContent = data.errors.map(e => `${e.filename}: ${e.error}`).join(" · ");
    }

    data.candidates.forEach(c => candidates[c.candidate_id] = c);
    renderTable();
  } catch (err) {
    hideStatus();
    errorBox.hidden = false;
    errorBox.textContent = err.message;
  } finally {
    analyzeBtn.disabled = false;
  }
});

// ---------- Render table ----------
function renderTable() {
  const list = Object.values(candidates).sort((a, b) => b.final_score - a.final_score);
  if (!list.length) return;

  emptyState.hidden = true;
  results.hidden = false;
  resultsCount.textContent = `${list.length} candidate${list.length > 1 ? "s" : ""} screened`;

  tbody.innerHTML = "";
  list.forEach(c => tbody.appendChild(renderRow(c)));
}

function scoreClass(score) {
  if (score === null) return "none";
  if (score >= 0.7) return "high";
  if (score >= 0.4) return "mid";
  return "low";
}

function renderRow(c) {
  const tr = document.createElement("tr");
  tr.dataset.id = c.candidate_id;

  const hasScore = c.final_score !== null;
  const pct = hasScore ? Math.round(c.final_score * 100) : null;
  const isNoMatch = c.target_job === "No clear match";

  const skillChips = (c.top_skills || []).length
    ? c.top_skills.map(s => `<span class="chip matched table-chip">${s}</span>`).join("")
    : `<span class="chip-empty">None detected</span>`;

  tr.innerHTML = `
    <td>
      <div class="candidate-name">${c.name}</div>
      <div class="candidate-years">${c.years_experience} yrs experience</div>
    </td>
    <td><span class="target-role-text ${isNoMatch ? "no-match-text" : ""}">${c.target_job}</span></td>
    <td>${hasScore ? `<span class="match-score ${scoreClass(c.final_score)}">${pct}%</span>` : `<span class="match-score none">—</span>`}</td>
    <td><span class="gap-count">${hasScore ? `${c.skill_gaps.length} gap${c.skill_gaps.length !== 1 ? "s" : ""}` : "—"}</span></td>
    <td><div class="chip-row table-chip-row">${skillChips}</div></td>
    <td><span class="status-pill ${c.status}">${statusLabel(c.status)}</span></td>
    <td>
      <div class="row-actions">
        <button class="action-btn select-btn" ${c.status !== "pending" ? "disabled" : ""}>Select</button>
        <button class="action-btn reject-btn" ${c.status !== "pending" ? "disabled" : ""}>Reject</button>
        <button class="action-btn view-btn" ${c.status === "pending" ? "hidden" : ""}>View</button>
      </div>
    </td>
  `;

  tr.querySelector(".select-btn").addEventListener("click", () => selectCandidate(c.candidate_id));
  tr.querySelector(".reject-btn").addEventListener("click", () => rejectCandidate(c.candidate_id));
  const viewBtn = tr.querySelector(".view-btn");
  if (viewBtn) viewBtn.addEventListener("click", () => openModal(c.candidate_id));

  return tr;
}

function statusLabel(status) {
  return { pending: "Pending", selected: "Selected", rejected: "Rejected" }[status] || status;
}

// ---------- Actions ----------
async function selectCandidate(id) {
  const resp = await fetch(`/api/select/${id}`, { method: "POST" });
  const data = await resp.json();
  if (resp.ok) {
    candidates[id].status = data.status;
    candidates[id].selection_message = data.selection_message;
    renderTable();
    openModal(id);
  }
}

async function rejectCandidate(id) {
  openModal(id, /* generating */ true);
  const resp = await fetch(`/api/reject/${id}`, { method: "POST" });
  const data = await resp.json();
  if (!resp.ok) {
    modalLoading.hidden = true;
    modalBody.hidden = false;
    modalBody.innerHTML = `<p class="error-box" style="display:block;">${data.error}</p>`;
    return;
  }
  candidates[id].status = "rejected";
  candidates[id].roadmap = data.roadmap;
  candidates[id].rejection_message = data.rejection_message;
  renderTable();
  renderModalContent(candidates[id]);
}

// ---------- Modal ----------
function openModal(id, generating) {
  modalOverlay.hidden = false;
  if (generating) {
    modalLoading.hidden = false;
    modalBody.hidden = true;
  } else {
    renderModalContent(candidates[id]);
  }
}

function closeModal() {
  modalOverlay.hidden = true;
  modalLoading.hidden = true;
  modalBody.hidden = true;
}
modalClose.addEventListener("click", closeModal);
modalOverlay.addEventListener("click", (e) => { if (e.target === modalOverlay) closeModal(); });

function renderModalContent(c) {
  modalLoading.hidden = true;
  modalBody.hidden = false;

  if (c.status === "selected") {
    modalBody.innerHTML = `
      <h3 class="modal-section-title">${c.name} — ${c.target_job}</h3>
      <h4 class="modal-section-title">Selection message</h4>
      <div class="message-box" id="selection-text">${(c.selection_message || "").replace(/</g, "&lt;")}</div>
      <button class="copy-btn" id="copy-msg-btn">Copy message</button>
    `;
    document.getElementById("copy-msg-btn").addEventListener("click", (e) => {
      navigator.clipboard.writeText(c.selection_message || "");
      e.target.textContent = "Copied!";
      e.target.classList.add("copied");
      setTimeout(() => { e.target.textContent = "Copy message"; e.target.classList.remove("copied"); }, 1800);
    });
    return;
  }

  const roadmap = c.roadmap || {};
  const allResources = roadmap.recommended_resources || [];

  const phasesHtml = (roadmap.roadmap || []).map(p => {
    const skillTags = (p.skills || []).map(s => `<span>${s}</span>`).join("");
    const resourcesHtml = (p.skills || []).map(skill => {
      const skillResources = allResources.filter(r => r.skill === skill);
      if (skillResources.length) {
        return skillResources.map(r => `
          <a class="phase-resource-link" href="${r.resource_url}" target="_blank" rel="noopener">
            <span>${r.resource_name}</span>
            <span class="phase-resource-type">${r.resource_type}</span>
          </a>`).join("");
      }
      return `<span class="no-resource-fallback">No verified resource on file for <strong>${skill}</strong> yet — try a small personal project using it, or check its official docs / a well-known course platform directly.</span>`;
    }).join("");

    return `
      <div class="phase-card">
        <h5 class="phase-card-name">${p.phase_name}</h5>
        <p class="phase-card-goal">${p.goal || ""}</p>
        <div class="phase-card-skills">${skillTags}</div>
        <div class="phase-resource-list">${resourcesHtml}</div>
      </div>
    `;
  }).join("");

  const feedbackHtml = (roadmap.resume_improvements || []).length
    ? `<ol class="feedback-mini-list">${roadmap.resume_improvements.map(f => `<li>${f}</li>`).join("")}</ol>`
    : "";

  modalBody.innerHTML = `
    <h3 class="modal-section-title">${c.name} — ${c.target_job}</h3>
    <p style="font-size:13px;color:var(--ink-soft);">${roadmap.career_summary || ""}</p>

    <h4 class="modal-section-title">Personalized roadmap</h4>
    ${phasesHtml || "<p>No gaps — this candidate matched every required skill.</p>"}

    ${feedbackHtml ? `<h4 class="modal-section-title">Resume feedback</h4>${feedbackHtml}` : ""}

    <h4 class="modal-section-title">Rejection message</h4>
    <div class="message-box" id="rejection-text">${(c.rejection_message || "").replace(/</g, "&lt;")}</div>
    <button class="copy-btn" id="copy-msg-btn">Copy message</button>
  `;

  document.getElementById("copy-msg-btn").addEventListener("click", (e) => {
    navigator.clipboard.writeText(c.rejection_message || "");
    e.target.textContent = "Copied!";
    e.target.classList.add("copied");
    setTimeout(() => { e.target.textContent = "Copy message"; e.target.classList.remove("copied"); }, 1800);
  });
}
