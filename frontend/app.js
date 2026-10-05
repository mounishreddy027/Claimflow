// ClaimFlow Client-Side Application Engine
const API_BASE =
  window.location.port === "8000"
    ? ""
    : `${window.location.protocol}//${window.location.hostname || "127.0.0.1"}:8000`;

let appState = {
  claims: [],
  policies: [],
  currentClaim: null,
  config: null,
};

// Initialize application
document.addEventListener("DOMContentLoaded", () => {
  // Set default incident date to today
  const dateInput = document.getElementById("intakeIncidentDate");
  if (dateInput) {
    dateInput.value = new Date().toISOString().split("T")[0];
  }
  refreshData();
});

// Toast notification helper
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  const bgClass =
    type === "success"
      ? "bg-emerald-600 text-white"
      : type === "error"
      ? "bg-rose-600 text-white"
      : "bg-blue-600 text-white";

  toast.className = `${bgClass} px-4 py-3 rounded-xl shadow-xl text-xs font-semibold flex items-center space-x-2 transition-all transform duration-300 pointer-events-auto`;
  toast.innerHTML = `
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Tab navigation switcher
function switchTab(tabId) {
  const tabs = ["dashboard", "intake", "fraud", "documents", "assessment", "audit"];
  tabs.forEach((t) => {
    const section = document.getElementById(`section-${t}`);
    const tabBtn = document.getElementById(`tab-${t}`);
    if (t === tabId) {
      if (section) section.classList.remove("hidden");
      if (tabBtn) {
        tabBtn.className = "nav-tab px-3.5 py-2 text-sm font-medium rounded-lg transition text-white bg-blue-600 shadow-sm flex items-center space-x-1.5";
      }
    } else {
      if (section) section.classList.add("hidden");
      if (tabBtn) {
        tabBtn.className = "nav-tab px-3.5 py-2 text-sm font-medium rounded-lg transition text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 flex items-center space-x-1.5";
      }
    }
  });

  if (tabId === "dashboard") refreshData();
}

// Refresh core data
async function refreshData() {
  await Promise.all([fetchSystemConfig(), fetchPolicies(), fetchClaims()]);
}

// 1. Fetch system configuration (AI mode vs Fallback)
async function fetchSystemConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/system/config`);
    if (res.ok) {
      const data = await res.json();
      appState.config = data;

      const aiModeBadge = document.getElementById("aiModeBadge");
      const aiModeText = document.getElementById("aiModeText");
      const statFraudMode = document.getElementById("statFraudMode");
      const statFraudSubtext = document.getElementById("statFraudSubtext");

      if (data.aiConfigured) {
        aiModeBadge.className = "flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-purple-500/10 text-purple-300 border border-purple-500/30";
        aiModeText.textContent = `AI Active (${data.aiProvider.toUpperCase()} - ${data.aiModel})`;
        statFraudMode.textContent = `AI Powered (${data.aiProvider.toUpperCase()})`;
        statFraudMode.className = "text-lg font-bold text-purple-400 mt-1";
        statFraudSubtext.textContent = `Model: ${data.aiModel} (fallback ready)`;
      } else {
        aiModeBadge.className = "flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700";
        aiModeText.textContent = "Deterministic Fallback (FR-01 to FR-06)";
        statFraudMode.textContent = "Deterministic Fallback";
        statFraudMode.className = "text-lg font-bold text-slate-300 mt-1";
        statFraudSubtext.textContent = "Add GEMINI_API_KEY in .env for AI";
      }
    }
  } catch (err) {
    console.error("Config fetch error:", err);
  }
}

// 2. Fetch policies registry
async function fetchPolicies() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/policies`);
    if (res.ok) {
      appState.policies = await res.json();
      populatePolicySelect();
    }
  } catch (err) {
    console.error("Policies fetch error:", err);
  }
}

function populatePolicySelect() {
  const sel = document.getElementById("intakePolicySelect");
  if (!sel) return;
  sel.innerHTML = '<option value="">-- Choose registered policy --</option>';

  appState.policies.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.policyNumber;
    opt.textContent = `${p.policyNumber} — ${p.lineOfBusiness} [${p.status}] (Sum: $${Number(p.sumInsured).toLocaleString()})`;
    sel.appendChild(opt);
  });
}

function onPolicySelected() {
  const sel = document.getElementById("intakePolicySelect");
  const polNum = sel.value;
  const policy = appState.policies.find((p) => p.policyNumber === polNum);
  const infoBox = document.getElementById("policyInfoBox");
  const claimTypeSel = document.getElementById("intakeClaimType");

  if (!policy) {
    infoBox.classList.add("hidden");
    return;
  }

  claimTypeSel.value = policy.lineOfBusiness;
  infoBox.classList.remove("hidden");
  infoBox.innerHTML = `
    <div class="flex justify-between items-center mb-1">
      <span class="font-bold text-slate-200">${policy.policyNumber}</span>
      <span class="px-2 py-0.5 rounded text-xs ${policy.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}">${policy.status}</span>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-400 mt-1">
      <div>Effective: <span class="text-slate-200">${policy.effectiveDate}</span></div>
      <div>Expires: <span class="text-slate-200">${policy.expiryDate || 'N/A'}</span></div>
      <div>Deductible: <span class="text-slate-200">$${policy.deductible}</span></div>
      <div>Co-Pay: <span class="text-slate-200">${policy.copayPercent}%</span></div>
    </div>
  `;
}

// 3. Fetch all claims
async function fetchClaims() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/claims`);
    if (res.ok) {
      appState.claims = await res.json();
      updateDashboardStats();
      renderClaimsTable();
      populateClaimSelects();
    }
  } catch (err) {
    console.error("Claims fetch error:", err);
  }
}

function updateDashboardStats() {
  document.getElementById("statTotalClaims").textContent = appState.claims.length;
  document.getElementById("statUnderReview").textContent = appState.claims.filter(
    (c) => c.status === "UNDER_REVIEW" || c.status === "FILED"
  ).length;
  document.getElementById("statSettled").textContent = appState.claims.filter(
    (c) => c.status === "SETTLED" || c.status === "APPROVED"
  ).length;
}

function renderClaimsTable() {
  const tbody = document.getElementById("claimsTableBody");
  const filter = document.getElementById("filterStatus").value;
  if (!tbody) return;

  const filtered = filter === "ALL"
    ? appState.claims
    : appState.claims.filter((c) => c.status === filter);

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="px-6 py-8 text-center text-slate-500">
          No claims found matching status '${filter}'.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered
    .map((c) => {
      const statusBadge = getStatusBadge(c.status);
      return `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="px-6 py-3.5 font-mono text-xs font-semibold text-blue-400">${c.claimId}</td>
          <td class="px-6 py-3.5 font-mono text-xs text-slate-300">${c.policyNumber}</td>
          <td class="px-6 py-3.5 text-xs text-slate-300 font-medium">${c.claimType}</td>
          <td class="px-6 py-3.5 font-mono text-xs font-bold text-white">$${Number(c.claimAmount).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
          <td class="px-6 py-3.5">${statusBadge}</td>
          <td class="px-6 py-3.5 text-xs text-slate-400">${c.incidentDate}</td>
          <td class="px-6 py-3.5 text-right space-x-1.5">
            <button onclick="inspectClaim('${c.claimId}')" class="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 transition">Inspect</button>
            <button onclick="inspectFraud('${c.claimId}')" class="px-2.5 py-1 text-xs font-medium rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/30 transition">AI Screener</button>
          </td>
        </tr>
      `;
    })
    .join("");
}

function getStatusBadge(status) {
  const map = {
    FILED: "bg-slate-700/60 text-slate-300 border-slate-600",
    UNDER_REVIEW: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    APPROVED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    SETTLED: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    REJECTED: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    REOPENED: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  };
  const cls = map[status] || "bg-slate-800 text-slate-400 border-slate-700";
  return `<span class="px-2.5 py-1 rounded-full text-xs font-bold border ${cls}">${status}</span>`;
}

function populateClaimSelects() {
  const selects = ["fraudClaimSelect", "docClaimSelect", "assessmentClaimSelect", "auditClaimSelect"];
  selects.forEach((id) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">-- Choose Claim --</option>';
    appState.claims.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.claimId;
      opt.textContent = `${c.claimId} (${c.claimType}, $${c.claimAmount}) — [${c.status}]`;
      sel.appendChild(opt);
    });
    if (currentVal && appState.claims.some((c) => c.claimId === currentVal)) {
      sel.value = currentVal;
    }
  });
}

// 4. Submit FNOL Claim
async function handleIntakeSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById("btnSubmitFnol");
  btn.disabled = true;
  btn.textContent = "Validating & Submitting...";

  const policyNumber = document.getElementById("intakePolicySelect").value;
  const claimType = document.getElementById("intakeClaimType").value;
  const claimAmount = parseFloat(document.getElementById("intakeClaimAmount").value);
  const incidentDate = document.getElementById("intakeIncidentDate").value;
  const incidentDescription = document.getElementById("intakeDescription").value;

  const docs = [];
  if (document.getElementById("attachDoc1").checked) {
    const type = claimType === "MOTOR" ? "POLICE_FIR" : claimType === "HEALTH" ? "HOSPITAL_BILL" : "DEATH_CERTIFICATE";
    docs.push({ documentType: type, fileName: `${type.toLowerCase()}_initial.pdf` });
  }
  if (document.getElementById("attachDoc2").checked) {
    const type = claimType === "MOTOR" ? "REPAIR_INVOICE" : claimType === "HEALTH" ? "DISCHARGE_SUMMARY" : "AUTOPSY_REPORT";
    docs.push({ documentType: type, fileName: `${type.toLowerCase()}_initial.pdf` });
  }

  const payload = {
    policyNumber,
    incidentDate,
    claimType,
    claimAmount,
    incidentDescription,
    supportingDocuments: docs,
  };

  try {
    const res = await fetch(`${API_BASE}/api/v1/claims/intake`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      showToast(`Intake Failed: ${data.message || data.detail || "Validation Error"}`, "error");
    } else {
      showToast(`Claim ${data.claimId} filed successfully! Status: FILED`, "success");
      await refreshData();
      switchTab("dashboard");
    }
  } catch (err) {
    showToast(`Network Error: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Submit FNOL Claim";
  }
}

// 5. Fraud Screening Engine Interaction (AI vs Fallback)
async function runFraudEvaluation(forceDeterministic = false) {
  const claimId = document.getElementById("fraudClaimSelect").value;
  const container = document.getElementById("fraudResultContainer");
  if (!claimId) {
    showToast("Please select a claim to evaluate.", "error");
    return;
  }

  container.innerHTML = `
    <div class="p-8 text-center text-slate-400">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mb-3"></div>
      <p class="font-semibold text-sm text-slate-200">${forceDeterministic ? "Executing Deterministic Rule Engine (FR-01 to FR-06)..." : "Connecting to AI LLM Engine for Non-Deterministic Fraud Screening..."}</p>
      <p class="text-xs text-slate-500 mt-1">Analyzing claim patterns, inception dates, and loss narrative</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/v1/claims/${claimId}/fraud-screen`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ forceDeterministic }),
    });

    if (!res.ok) {
      const err = await res.json();
      container.innerHTML = `<div class="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs">${err.detail || "Error evaluating fraud"}</div>`;
      return;
    }

    const data = await res.json();
    renderFraudResults(data);
  } catch (err) {
    container.innerHTML = `<div class="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl text-xs">${err.message}</div>`;
  }
}

function renderFraudResults(res) {
  const container = document.getElementById("fraudResultContainer");
  const isFlagged = res.isFlagged;
  const isAi = res.evaluationMode === "AI_POWERED";

  const modeBadge = isAi
    ? `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">AI-POWERED EVALUATION</span>`
    : `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-slate-700 text-slate-300 border border-slate-600">DETERMINISTIC FALLBACK (FR-01 - FR-06)</span>`;

  const flagBadge = isFlagged
    ? `<span class="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">FLAGGED FOR MANUAL REVIEW</span>`
    : `<span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">PASSED FRAUD SCREENING</span>`;

  let rulesHtml = "";
  if (res.triggeredRules && res.triggeredRules.length > 0) {
    rulesHtml = res.triggeredRules
      .map(
        (r) => `
      <div class="p-3 bg-slate-900/60 border border-slate-700/60 rounded-xl flex items-start space-x-3">
        <span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 text-xs font-mono font-bold">+${r.weight}</span>
        <div class="flex-1">
          <p class="text-xs font-bold text-white">${r.ruleId} — ${r.reasonCode}</p>
          <p class="text-xs text-slate-400 mt-0.5">${r.description}</p>
        </div>
      </div>
    `
      )
      .join("");
  } else {
    rulesHtml = `<div class="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-300">No anomaly or fraud rules triggered for this claim.</div>`;
  }

  container.innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-5 rounded-2xl bg-slate-900/60 border ${isFlagged ? 'border-rose-500/40 bg-rose-950/10' : 'border-slate-700/70'}">
        <p class="text-xs uppercase font-semibold text-slate-400">Fraud Risk Score</p>
        <div class="flex items-baseline space-x-2 mt-2">
          <span class="text-4xl font-extrabold ${isFlagged ? 'text-rose-400' : 'text-emerald-400'}">${res.fraudScore}</span>
          <span class="text-xs text-slate-500">/ 100</span>
        </div>
        <p class="text-xs text-slate-400 mt-2">Policy threshold: <span class="font-mono text-slate-200">${res.policyThreshold}</span></p>
      </div>

      <div class="p-5 rounded-2xl bg-slate-900/60 border border-slate-700/70">
        <p class="text-xs uppercase font-semibold text-slate-400">Screening Result</p>
        <div class="mt-3">${flagBadge}</div>
        <div class="mt-3">${modeBadge}</div>
      </div>

      <div class="p-5 rounded-2xl bg-slate-900/60 border border-slate-700/70">
        <p class="text-xs uppercase font-semibold text-slate-400">Report Metadata</p>
        <p class="text-xs font-mono text-slate-200 mt-2">Report ID: ${res.reportId}</p>
        <p class="text-xs text-slate-400 mt-1">Evaluated: ${new Date(res.evaluatedAt).toLocaleTimeString()}</p>
        ${res.aiConfidence ? `<p class="text-xs text-purple-300 mt-1">AI Confidence: ${(res.aiConfidence * 100).toFixed(0)}%</p>` : ''}
      </div>
    </div>

    <!-- AI Narrative / Explanation -->
    <div class="p-5 rounded-2xl bg-slate-900/80 border border-indigo-500/30">
      <h3 class="text-xs uppercase font-bold text-indigo-400 mb-2 flex items-center space-x-1.5">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        <span>Risk & Anomaly Narrative Analysis</span>
      </h3>
      <p class="text-sm text-slate-300 leading-relaxed">${res.aiAnalysis || "Evaluation complete."}</p>
    </div>

    <!-- Triggered Rules Breakdown -->
    <div class="space-y-3">
      <h3 class="text-xs uppercase font-bold text-slate-400">Triggered Rules & Weights</h3>
      <div class="space-y-2">${rulesHtml}</div>
    </div>
  `;
}

function inspectFraud(claimId) {
  switchTab("fraud");
  const sel = document.getElementById("fraudClaimSelect");
  if (sel) {
    sel.value = claimId;
    runFraudEvaluation(false);
  }
}

function inspectClaim(claimId) {
  switchTab("documents");
  const sel = document.getElementById("docClaimSelect");
  if (sel) {
    sel.value = claimId;
    loadClaimDocuments();
  }
}

// 6. Document Verification Workflow
async function loadClaimDocuments() {
  const claimId = document.getElementById("docClaimSelect").value;
  const container = document.getElementById("docVerificationContainer");
  if (!claimId) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/claims/${claimId}/documents`);
    if (!res.ok) {
      container.innerHTML = `<div class="p-4 text-xs text-rose-400">Failed to load documents</div>`;
      return;
    }

    const data = await res.json();
    const docs = data.documents;

    let itemsHtml = docs
      .map(
        (d) => `
      <div class="p-4 bg-slate-900/60 border border-slate-700/60 rounded-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <div class="flex items-center space-x-2">
            <span class="text-xs font-mono font-bold text-white">${d.documentType}</span>
            <span class="px-2 py-0.5 rounded text-xs font-semibold ${d.status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}">${d.status}</span>
          </div>
          <p class="text-xs text-slate-400 mt-1">${d.fileName} &middot; ID: <span class="font-mono text-slate-300">${d.documentId}</span></p>
        </div>
        <div class="flex items-center space-x-2">
          ${
            d.status !== "VERIFIED"
              ? `
            <button onclick="verifyDoc('${claimId}', '${d.documentId}', 'VERIFY')" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition">Verify</button>
            <button onclick="verifyDoc('${claimId}', '${d.documentId}', 'REJECT')" class="px-3 py-1.5 rounded-lg bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 text-xs font-semibold border border-rose-500/30 transition">Reject</button>
          `
              : `<span class="text-xs text-emerald-400 font-semibold flex items-center space-x-1"><span>✓ Verified</span></span>`
          }
        </div>
      </div>
    `
      )
      .join("");

    container.innerHTML = `
      <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-700/60 flex justify-between items-center text-xs">
        <div>
          <span class="font-bold text-white">Checklist Status:</span>
          <span class="ml-1 text-slate-300">${data.checklistStatus} (${data.verifiedCount} / ${data.mandatoryCount} Verified)</span>
        </div>
        <div>
          ${data.checklistStatus === "COMPLETE" ? '<span class="text-emerald-400 font-bold">✓ Ready for Assessment</span>' : '<span class="text-amber-400">Pending mandatory documents</span>'}
        </div>
      </div>
      <div class="space-y-3 mt-4">${itemsHtml}</div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="p-4 text-xs text-rose-400">${err.message}</div>`;
  }
}

async function verifyDoc(claimId, docId, action) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/claims/${claimId}/documents/${docId}/verify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Actor-Role": "ROLE_ASSESSOR",
      },
      body: JSON.stringify({ action, notes: `${action} via ClaimFlow Frontend` }),
    });

    if (res.ok) {
      showToast(`Document ${docId} marked ${action}!`, "success");
      await refreshData();
      await loadClaimDocuments();
    } else {
      const err = await res.json();
      showToast(`Failed: ${err.detail || "Error"}`, "error");
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
}

// 7. Assessment & Settlement Interaction
function loadAssessmentPreview() {
  const claimId = document.getElementById("assessmentClaimSelect").value;
  const content = document.getElementById("assessmentFormContent");
  const settlementBox = document.getElementById("settlementActionBox");

  if (!claimId) {
    content.classList.add("hidden");
    settlementBox.innerHTML = '<div class="p-8 text-center text-slate-500 text-xs">Select or assess an approved claim to unlock settlement and payout ledger recording.</div>';
    return;
  }

  const claim = appState.claims.find((c) => c.claimId === claimId);
  const policy = appState.policies.find((p) => p.policyNumber === claim.policyNumber);

  content.classList.remove("hidden");
  document.getElementById("asSumInsured").textContent = `$${Number(policy ? policy.sumInsured : 50000).toLocaleString()}`;
  document.getElementById("asClaimAmount").textContent = `$${Number(claim.claimAmount).toLocaleString()}`;
  document.getElementById("asDeductible").textContent = `$${Number(policy ? policy.deductible : 0).toLocaleString()}`;
  document.getElementById("asCopay").textContent = `${policy ? policy.copayPercent : 0}%`;

  if (claim.status === "APPROVED") {
    settlementBox.innerHTML = `
      <div class="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 space-y-4">
        <div class="flex items-center space-x-2">
          <span class="w-3 h-3 rounded-full bg-emerald-400"></span>
          <h3 class="text-sm font-bold text-white">Claim is APPROVED & Ready for Payout</h3>
        </div>
        <p class="text-xs text-slate-400">All checks and coverage limits evaluated. Ready to disburse payout to WORM immutable ledger.</p>
        <button onclick="disburseSettlement('${claimId}')" class="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-500/20 transition">
          Confirm Settlement & Disburse Payout
        </button>
      </div>
    `;
  } else if (claim.status === "SETTLED") {
    settlementBox.innerHTML = `
      <div class="p-5 rounded-2xl bg-blue-950/20 border border-blue-500/30 text-xs space-y-2">
        <p class="font-bold text-blue-300">✓ Claim SETTLED (Immutable Payout Recorded)</p>
        <p class="text-slate-400">Disbursed on STUBBED_ACH rail. Can be reopened under dispute workflow.</p>
      </div>
    `;
  } else {
    settlementBox.innerHTML = `
      <div class="p-5 rounded-2xl bg-slate-900/60 border border-slate-700/60 text-xs text-slate-400">
        Claim is in state <span class="font-bold text-slate-200">${claim.status}</span>. Must advance to APPROVED to unlock settlement.
      </div>
    `;
  }
}

async function submitAssessment() {
  const claimId = document.getElementById("assessmentClaimSelect").value;
  const addDeduct = parseFloat(document.getElementById("additionalDeductible").value) || 0;
  const notes = document.getElementById("assessorNotes").value;

  try {
    const res = await fetch(`${API_BASE}/api/v1/claims/${claimId}/assess`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Actor-Role": "ROLE_ASSESSOR",
      },
      body: JSON.stringify({
        additionalDeductible: addDeduct,
        assessorNotes: notes,
      }),
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`Assessment completed! Payable amount: $${data.payableAmount}`, "success");
      await refreshData();
      loadAssessmentPreview();
    } else {
      const err = await res.json();
      showToast(`Assessment Failed: ${err.detail || "Error"}`, "error");
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
}

async function disburseSettlement(claimId) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/claims/${claimId}/settle`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Actor-Role": "ROLE_ADMIN",
      },
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`Settlement Recorded! Payout ID: ${data.payoutId} for $${data.payoutAmount}`, "success");
      await refreshData();
      loadAssessmentPreview();
    } else {
      const err = await res.json();
      showToast(`Settlement Failed: ${err.detail || "Error"}`, "error");
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
}

// 8. Cryptographic Audit Trail
async function loadAuditTrail() {
  const claimId = document.getElementById("auditClaimSelect").value;
  const container = document.getElementById("auditLogContainer");
  if (!claimId) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/audit-trail/${claimId}`);
    if (!res.ok) {
      container.innerHTML = `<div class="p-4 text-xs text-rose-400">Failed to load audit trail</div>`;
      return;
    }

    const data = await res.json();
    if (!data || data.length === 0) {
      container.innerHTML = `<div class="p-8 text-center text-slate-500 text-xs">No audit events recorded for ${claimId}</div>`;
      return;
    }

    container.innerHTML = data
      .map(
        (log, idx) => `
      <div class="p-4 rounded-xl bg-slate-900/70 border border-slate-700/60 font-mono text-xs space-y-2">
        <div class="flex justify-between items-center text-slate-400">
          <span class="text-blue-400 font-bold">#${idx + 1} &middot; ${log.operationType}</span>
          <span class="text-slate-500">${log.timestamp}</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300">
          <div>Actor: <span class="text-white">${log.actorId}</span> (${log.actorRole})</div>
          <div>Transition: <span class="text-amber-300">${log.previousState || 'None'}</span> &rarr; <span class="text-emerald-300">${log.newState}</span></div>
        </div>
        <div class="pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 space-y-1 overflow-x-auto">
          <div>SHA256 Entry Hash: <span class="text-slate-300 select-all">${log.entryHash}</span></div>
          <div>Prev Hash: <span class="text-slate-400 select-all">${log.previousHash}</span></div>
        </div>
      </div>
    `
      )
      .join("");
  } catch (err) {
    container.innerHTML = `<div class="p-4 text-xs text-rose-400">${err.message}</div>`;
  }
}
