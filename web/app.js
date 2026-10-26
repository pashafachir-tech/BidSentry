import { api } from "./api.js";
import { getState, setState, subscribe } from "./state.js";
import { renderApp } from "./render.js";
import { getReviewSnapshot } from "./review.js";

const root = document.getElementById("app");
const toastNode = document.getElementById("toast");
const uploadedFiles = { dok_pemilihan: [], adendum: [], pustaka: [], contract_draft: [], baseline_contract: [] };
const uploadErrors = { dok_pemilihan: [], adendum: [], pustaka: [], contract_draft: [], baseline_contract: [] };
const auditSubmitReadyMarkup = 'Jalankan audit <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
const MAX_FILES_PER_UPLOAD = 20;
const MAX_PARALLEL_EXTRACTIONS = 3;
let workspaceRequestSequence = 0;
let activeUploads = 0;
let pendingDispatchPayload = null;
let dispatchInProgress = false;

try {
  document.documentElement.dataset.theme = localStorage.getItem("bidsentry-theme") === "dark" ? "dark" : "light";
} catch {
  document.documentElement.dataset.theme = "light";
}

function render() {
  const active = document.activeElement;
  const id = active?.id;
  const start = typeof active?.selectionStart === "number" ? active.selectionStart : null;
  const action = root.contains(active) ? active?.dataset?.action : null;
  const actionIndex = action
    ? [...root.querySelectorAll("[data-action]")].filter((node) => node.dataset.action === action).indexOf(active)
    : -1;
  root.innerHTML = renderApp(getState());
  const next = (id && document.getElementById(id)) || (action && [...root.querySelectorAll("[data-action]")].filter((node) => node.dataset.action === action)[actionIndex]);
  if (next) {
    next.focus({ preventScroll: true });
    if (start !== null && typeof next.setSelectionRange === "function") next.setSelectionRange(start, start);
  }
}

subscribe(render);

function toast(message, kind = "success") {
  toastNode.className = "toast";
  void toastNode.offsetWidth;
  toastNode.textContent = message;
  toastNode.className = `toast toast-visible ${kind === "error" ? "toast-error" : ""}`;
}

async function loadWorkspace({ preserveSelection = true, includeOverview = true, includeHealth = true, includeFeedback = true } = {}) {
  const requestSequence = ++workspaceRequestSequence;
  setState({ loading: true });
  const state = getState();
  try {
    const [overview, audits, health, reviewFeedback] = await Promise.all([
      includeOverview ? api.overview() : Promise.resolve(state.overview),
      api.audits({ q: state.query, risk: state.riskFilter }),
      includeHealth ? api.health() : Promise.resolve(null),
      includeFeedback ? api.reviewFeedback(state.customReview?.audit_id || "").catch(() => null) : Promise.resolve(state.reviewFeedback),
    ]);
    if (requestSequence !== workspaceRequestSequence) return;
    const selected = preserveSelection && audits.audits.some((row) => row.audit_id === state.selectedAuditId)
      ? state.selectedAuditId : audits.audits[0]?.audit_id || null;
    setState({
      ...(includeOverview ? { overview } : {}),
      audits: audits.audits,
      selectedAuditId: selected,
      ...(includeHealth && health ? { integrations: health.integrations } : {}),
      ...(includeFeedback ? { reviewFeedback } : {}),
      loading: false,
    });
  } catch (error) {
    if (requestSequence !== workspaceRequestSequence) return;
    setState({ loading: false });
    toast(error.message, "error");
  }
}

function openAuditDialog(draft = null) {
  const dialog = document.getElementById("audit-dialog");
  const form = document.getElementById("audit-form");
  if (draft && form) {
    for (const name of ["package_name", "tender_id", "notice_number", "pokja_name", "company_name", "contract_value_idr", "dok_pemilihan", "adendum", "pustaka", "contract_draft", "baseline_contract"]) {
      const field = form.elements.namedItem(name);
      if (field) field.value = draft[name] ?? "";
    }
    form.elements.namedItem("allow_external_processing").checked = Boolean(draft.allow_external_processing);
    form.elements.namedItem("review_role").value = draft.review_role || "procurement";
  }
  if (dialog?.showModal) dialog.showModal();
  else toast("Dialog audit tidak tersedia pada browser ini.", "error");
}

async function openSettingsDialog() {
  try {
    const settings = await api.integrationSettings();
    const form = document.getElementById("settings-form");
    if (!form) return;
    const set = (name, value) => { form.elements.namedItem(name).value = value ?? ""; };
    form.elements.namedItem("langflow_enabled").checked = Boolean(settings.langflow.enabled);
    set("langflow_url", settings.langflow.url);
    set("langflow_flow_id", settings.langflow.flow_id);
    set("langflow_api_key", "");
    set("langflow_timeout_seconds", settings.langflow.timeout_seconds);
    set("composio_api_key", "");
    set("composio_entity_id", settings.composio.entity_id);
    set("composio_base_url", settings.composio.base_url);
    set("composio_timeout_seconds", settings.composio.timeout_seconds);
    form.elements.namedItem("clear_langflow_api_key").checked = false;
    form.elements.namedItem("clear_composio_api_key").checked = false;
    document.getElementById("langflow-key-status").textContent = settings.langflow.api_key_saved ? "API key tersimpan" : "API key belum diatur";
    document.getElementById("composio-key-status").textContent = settings.composio.api_key_saved ? "API key tersimpan" : "Belum dikonfigurasi";
    document.getElementById("settings-file-status").textContent = settings.config_file_exists
      ? "Disimpan ke file .env lokal dan dibaca tanpa restart. API key tidak pernah ditampilkan kembali."
      : "File .env akan dibuat saat disimpan. API key tidak pernah ditampilkan kembali.";
    document.getElementById("settings-dialog")?.showModal();
  } catch (error) {
    toast(error.message || "Pengaturan tidak dapat dimuat.", "error");
  }
}

async function saveSettings(form) {
  const values = new FormData(form);
  const payload = {
    langflow_enabled: values.get("langflow_enabled") === "on",
    langflow_url: String(values.get("langflow_url") || "").trim(),
    langflow_flow_id: String(values.get("langflow_flow_id") || "").trim(),
    langflow_api_key: String(values.get("langflow_api_key") || ""),
    clear_langflow_api_key: values.get("clear_langflow_api_key") === "on",
    langflow_timeout_seconds: Number(values.get("langflow_timeout_seconds")),
    composio_api_key: String(values.get("composio_api_key") || ""),
    clear_composio_api_key: values.get("clear_composio_api_key") === "on",
    composio_entity_id: String(values.get("composio_entity_id") || "").trim(),
    composio_base_url: String(values.get("composio_base_url") || "").trim(),
    composio_timeout_seconds: Number(values.get("composio_timeout_seconds")),
  };
  const button = document.getElementById("save-settings");
  if (button) { button.disabled = true; button.textContent = "Menyimpan…"; }
  try {
    await api.saveIntegrationSettings(payload);
    document.getElementById("settings-dialog")?.close();
    toast("Pengaturan tersimpan ke .env. Status koneksi diperbarui.");
    await loadWorkspace({ includeOverview: false, includeFeedback: false });
  } catch (error) {
    toast(error.message || "Pengaturan gagal disimpan.", "error");
  } finally {
    if (button) { button.disabled = false; button.textContent = "Simpan koneksi"; }
  }
}

function clearUploadedFileLabels() {
  for (const field of Object.keys(uploadedFiles)) {
    uploadedFiles[field] = [];
    uploadErrors[field] = [];
    const list = document.getElementById(`${field}-files`);
    if (list) { list.textContent = ""; list.classList.remove("file-list-error"); }
  }
}

function renderFileNames(field) {
  const list = document.getElementById(`${field}-files`);
  if (!list) return;
  const messages = [...uploadedFiles[field], ...uploadErrors[field].map((item) => `Gagal · ${item.name ? `${item.name}: ` : ""}${item.message}`)];
  list.textContent = messages.join(" · ");
  list.classList.toggle("file-list-error", uploadErrors[field].length > 0);
}

async function ingestFiles(fileList, field) {
  const files = [...(fileList || [])];
  const textarea = document.querySelector(`[name="${field}"]`);
  if (!textarea || !files.length) return;
  if (files.length > MAX_FILES_PER_UPLOAD) {
    uploadErrors[field].push({ name: "", message: `maksimal ${MAX_FILES_PER_UPLOAD} file dalam satu kali unggah.` });
    renderFileNames(field);
    toast(`Pilih maksimal ${MAX_FILES_PER_UPLOAD} file dalam satu kali unggah.`, "error");
    return;
  }
  const submit = document.getElementById("submit-audit");
  activeUploads += 1;
  if (submit) { submit.disabled = true; submit.textContent = "Membaca file…"; }
  const zone = root.querySelector(`.drop-zone[data-drop-target="${field}"]`);
  if (zone) zone.classList.add("is-reading");
  try {
    const results = [];
    for (let offset = 0; offset < files.length; offset += MAX_PARALLEL_EXTRACTIONS) {
      const batch = await Promise.all(files.slice(offset, offset + MAX_PARALLEL_EXTRACTIONS).map(async (file) => {
        try {
          if (file.size > 8 * 1024 * 1024) throw new Error("ukuran maksimum 8 MB.");
          return { ok: true, file, data: await api.extractDocument(file) };
        } catch (error) {
          return { ok: false, file, message: error.message || "file tidak dapat dibaca." };
        }
      }));
      results.push(...batch);
    }
    const extracted = results.filter((item) => item.ok).map((item) => item.data);
    const failed = results.filter((item) => !item.ok);
    const attemptedNames = new Set(files.map((file) => file.name));
    uploadErrors[field] = uploadErrors[field].filter((item) => item.name && !attemptedNames.has(item.name));
    if (failed.length) uploadErrors[field].push(...failed.map((item) => ({ name: item.file.name, message: item.message })));
    let addedCount = 0;
    if (extracted.length) {
      const additions = extracted.map((item) => `--- ${item.filename} ---\n${item.text}`).join("\n\n");
      if (textarea.value.length + additions.length + 2 > 1_000_000) {
        uploadErrors[field].push(...extracted.map((item) => ({ name: item.filename, message: "gabungan teks melebihi 1.000.000 karakter; file ini tidak dimasukkan." })));
      } else {
        textarea.value = `${textarea.value.trim()}${textarea.value.trim() ? "\n\n" : ""}${additions}`;
        uploadedFiles[field].push(...extracted.map((item) => `${item.filename} (${new Intl.NumberFormat("id-ID").format(item.characters)} karakter)`));
        const addedNames = new Set(extracted.map((item) => item.filename));
        uploadErrors[field] = uploadErrors[field].filter((item) => !addedNames.has(item.name));
        addedCount = extracted.length;
      }
    }
    renderFileNames(field);
    if (field === "dok_pemilihan") {
      const packageInput = document.querySelector('[name="package_name"]');
      if (addedCount === 1 && packageInput && !packageInput.value.trim()) packageInput.value = extracted[0].filename.replace(/\.[^.]+$/, "");
    }
    const sectionName = field === "dok_pemilihan" ? "dokumen pemilihan" : field === "adendum" ? "adendum" : "bukti/kredensial";
    if (failed.length || uploadErrors[field].length) {
      const firstFailure = uploadErrors[field][0];
      toast(`${addedCount} file baru dibaca ke ${sectionName}; ${uploadErrors[field].length} file perlu diperiksa. ${firstFailure?.name ? `${firstFailure.name}: ` : ""}${firstFailure?.message || "Periksa daftar file."}`, "error");
    } else if (addedCount) {
      toast(`${addedCount} file berhasil dibaca ke bagian ${sectionName}.`);
    }
  } catch (error) {
    toast(error.message || "File tidak dapat dibaca.", "error");
  } finally {
    activeUploads = Math.max(0, activeUploads - 1);
    if (zone) zone.classList.remove("is-reading");
    const button = document.getElementById("submit-audit");
    if (button && activeUploads === 0) {
      button.disabled = false;
      button.innerHTML = auditSubmitReadyMarkup;
    }
  }
}

async function exportData() {
  try {
    const state = getState();
    const data = await api.audits({ q: state.query, risk: state.riskFilter });
    const workbook = await api.exportWorkbook({ kind: "register", audits: data.audits || [] });
    downloadWorkbook(workbook);
    toast("Register audit Excel berhasil disiapkan.");
  } catch (error) {
    toast(error.message, "error");
  }
}

function downloadWorkbook(workbook) {
  const binary = atob(workbook.content_base64 || "");
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  const blob = new Blob([bytes], { type: workbook.content_type || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = workbook.filename || "bidsentry-report.xlsx";
  link.click();
  requestAnimationFrame(() => URL.revokeObjectURL(url));
}

async function exportReview() {
  try {
    const state = getState();
    const snapshot = getReviewSnapshot(state);
    const workbook = await api.exportWorkbook({
      kind: "review",
      review: snapshot,
      include_ai_insights: state.reviewInsightsVisited,
    });
    downloadWorkbook(workbook);
    toast(state.reviewInsightsVisited ? "Excel Risk Review dan sheet AI Insights berhasil disiapkan." : "Excel Risk Review berhasil disiapkan.");
  } catch (error) {
    toast(error.message, "error");
  }
}

async function exportSelectedReview() {
  const state = getState();
  const selected = state.audits.find((item) => item.audit_id === state.selectedAuditId);
  if (!selected) {
    toast("Pilih paket terlebih dahulu untuk mengekspor Risk Review.", "error");
    return;
  }
  const isCurrentCustomReview = state.customReview?.audit_id === selected.audit_id;
  const review = isCurrentCustomReview ? getReviewSnapshot(state) : {
    package_name: selected.package_name,
    tender_id: selected.tender_id,
    agency: selected.agency,
    verdict: selected.verdict || "REVIEW_REQUIRED",
    risk_level: selected.risk_level,
    risk_score: selected.risk_score,
    contract_value_idr: selected.contract_value_idr,
    findings: Array.isArray(selected.findings) ? selected.findings : [],
    review_role: selected.review_role || "procurement",
    integrations: {},
  };
  try {
    const workbook = await api.exportWorkbook({
      kind: "review",
      review,
      include_ai_insights: isCurrentCustomReview && state.reviewInsightsVisited,
    });
    downloadWorkbook(workbook);
    toast(`Risk Review Excel untuk ${selected.package_name} berhasil disiapkan.`);
  } catch (error) {
    toast(error.message, "error");
  }
}

async function openObjection() {
  const state = getState();
  const review = getReviewSnapshot(state);
  if (!review.isCustom || !state.lastAuditDraft) { toast("Jalankan evaluasi terlebih dahulu.", "error"); return; }
  try {
    const result = await api.createSanggahan(buildSanggahanPayload(review, state, "markdown"));
    const bytes = Uint8Array.from(atob(result.content_base64), (char) => char.charCodeAt(0));
    document.getElementById("objection-draft").value = new TextDecoder().decode(bytes);
    document.getElementById("objection-dialog")?.showModal();
  } catch (error) { toast(error.message, "error"); }
}

function buildSanggahanPayload(review, state, format) {
  return {
    tender_id: review.tender_id || "", package_name: review.package_name || "", company_name: review.company_name || "",
    notice_number: review.notice_number || "", pokja_name: review.pokja_name || "",
    source_text: [state.lastAuditDraft?.dok_pemilihan, state.lastAuditDraft?.adendum, state.lastAuditDraft?.contract_draft].filter(Boolean).join("\n"),
    findings: review.findings || [], format,
  };
}

async function downloadObjectionDocx() {
  const state = getState();
  const review = getReviewSnapshot(state);
  if (!review.isCustom || !state.lastAuditDraft) { toast("Jalankan evaluasi terlebih dahulu.", "error"); return; }
  try {
    const result = await api.createSanggahan(buildSanggahanPayload(review, state, "docx"));
    const bytes = Uint8Array.from(atob(result.content_base64 || ""), (char) => char.charCodeAt(0));
    const blob = new Blob([bytes], { type: result.content_type || "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = result.filename || "draf-sanggahan.docx";
    link.click();
    requestAnimationFrame(() => URL.revokeObjectURL(url));
    toast("Draf sanggahan DOCX berhasil disiapkan untuk ditinjau.");
  } catch (error) { toast(error.message, "error"); }
}

function openDispatchConfirmation(useSelectedAudit = false) {
  if (dispatchInProgress) {
    toast("Tunggu sampai tindak lanjut yang sedang berjalan selesai.", "error");
    return;
  }
  const state = getState();
  const review = getReviewSnapshot(state);
  const selected = useSelectedAudit ? state.audits.find((item) => item.audit_id === state.selectedAuditId) : null;
  pendingDispatchPayload = selected ? {
    nama_paket: selected.package_name, verdict: selected.verdict, risk_score: selected.risk_score,
    alasan_utama: (selected.findings || []).slice(0, 5).map((item) => item.clause || item.evidence),
    tender_id: selected.tender_id,
  } : {
    nama_paket: review.package_name, verdict: review.verdict, risk_score: review.risk_score,
    alasan_utama: (review.findings || []).slice(0, 5).map((item) => item.clause || item.evidence),
    tender_id: review.tender_id,
  };
  const mode = state.integrations?.composio?.configured ? "Composio diatur; hasil aksi akan ditampilkan setelah layanan menjawab." : "Composio belum dikonfigurasi; aksi belum tersedia.";
  const configured = Boolean(state.integrations?.composio?.configured);
  document.getElementById("dispatch-confirm-copy").textContent = `${pendingDispatchPayload.nama_paket} · ${pendingDispatchPayload.verdict} · ${mode}`;
  document.getElementById("dispatch-live-consent-row").hidden = !configured;
  document.getElementById("dispatch-email-row").hidden = !configured;
  document.getElementById("dispatch-email").value = "";
  document.getElementById("dispatch-live-consent").checked = false;
  document.getElementById("dispatch-results").hidden = true;
  document.getElementById("dispatch-results").replaceChildren();
  const button = document.getElementById("confirm-dispatch-button");
  button.dataset.action = "confirm-dispatch";
  button.disabled = !configured;
  button.textContent = configured ? "Jalankan tindakan" : "Belum tersedia";
  document.getElementById("dispatch-dialog")?.showModal();
}

function showDispatchResult(result) {
  const panel = document.getElementById("dispatch-results");
  if (!panel) return;
  panel.replaceChildren();
  panel.hidden = false;
  const heading = document.createElement("strong");
  heading.textContent = result.status === "unavailable"
    ? "Konektor tidak tersedia · tidak ada tindakan dijalankan"
    : result.status === "error"
      ? "Konektor gagal · tidak ada hasil tindakan"
      : result.status === "partial"
        ? "Sebagian tindakan berhasil · periksa status tiap konektor"
        : "Semua tindakan workspace selesai";
  panel.append(heading);
  const actions = result.actions && typeof result.actions === "object" ? Object.entries(result.actions) : [];
  const labels = {
    GOOGLEDOCS_CREATE_DOCUMENT: ["Google Docs", result.doc_url],
    GOOGLECALENDAR_CREATE_EVENT: ["Google Calendar", result.event_url],
    GMAIL_CREATE_EMAIL_DRAFT: ["Draf Gmail", result.draft_url],
  };
  if (actions.length) {
    const list = document.createElement("ul");
    for (const [key, action] of actions) {
      const item = document.createElement("li");
      const [label, link] = labels[key] || [key, null];
      item.append(document.createTextNode(`${label}: ${action?.success ? "berhasil" : "gagal"}`));
      if (action?.success && typeof link === "string") {
        try {
          const url = new URL(link);
          if (url.protocol === "https:" && ["docs.google.com", "calendar.google.com", "mail.google.com"].includes(url.hostname)) {
            const anchor = document.createElement("a");
            anchor.href = url.href;
            anchor.target = "_blank";
            anchor.rel = "noopener noreferrer";
            anchor.textContent = "Buka";
            item.append(document.createTextNode(" · "), anchor);
          }
        } catch { /* Ignore connector links that are not safe web URLs. */ }
      }
      list.append(item);
    }
    panel.append(list);
  }
  const note = document.createElement("span");
  note.textContent = "Periksa hasil di workspace tujuan. Draf email tidak dikirim oleh BidSentry.";
  panel.append(note);
}

async function dispatchFollowUp() {
  if (dispatchInProgress) return;
  const button = document.getElementById("confirm-dispatch-button");
  const recipient = document.getElementById("dispatch-email");
  if (recipient?.value && !recipient.checkValidity()) {
    recipient.reportValidity();
    return;
  }
  if (button) { button.disabled = true; button.textContent = "Menyiapkan…"; }
  dispatchInProgress = true;
  try {
    const result = await api.dispatch({
      ...(pendingDispatchPayload || {}),
      email_penerima: String(document.getElementById("dispatch-email")?.value || "").trim(),
      allow_external_processing: Boolean(document.getElementById("dispatch-live-consent")?.checked),
    });
    showDispatchResult(result);
    const statusMessage = result.status === "success"
      ? "Semua tindakan workspace selesai. Periksa hasilnya sebelum digunakan."
      : result.status === "partial"
        ? "Sebagian tindakan workspace gagal. Periksa hasil tiap konektor."
        : result.status === "unavailable"
          ? "Composio belum dikonfigurasi; tidak ada tindakan yang dijalankan."
          : "Konektor tidak berhasil menjalankan tindakan.";
    toast(statusMessage, result.status === "partial" || result.status === "error" ? "error" : "success");
  } catch (error) {
    toast(error.message, "error");
    const panel = document.getElementById("dispatch-results");
    if (panel) { panel.hidden = false; panel.textContent = error.message; }
  } finally {
    dispatchInProgress = false;
    if (button) {
      button.disabled = false;
      button.dataset.action = "close-utility";
      button.textContent = "Selesai";
    }
  }
}

root.addEventListener("click", async (event) => {
  const dropZone = event.target.closest(".drop-zone");
  if (dropZone) {
    document.querySelector(`[data-file-input="${dropZone.dataset.dropTarget}"]`)?.click();
    return;
  }
  const target = event.target.closest("[data-action]");
  if (!target) return;
  const action = target.dataset.action;
  if (action === "new-audit") openAuditDialog();
  if (action === "open-settings") openSettingsDialog();
  if (action === "close-dialog") document.getElementById("audit-dialog")?.close();
  if (action === "close-utility") target.closest("dialog")?.close();
  if (action === "refresh") loadWorkspace();
  if (action === "theme-toggle") {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("bidsentry-theme", theme); } catch { /* Theme remains active for this page. */ }
    render();
  }
  if (action === "export") exportData();
  if (action === "export-review") exportReview();
  if (action === "export-selected-review") exportSelectedReview();
  if (action === "dispatch-selected") openDispatchConfirmation(true);
  if (action === "open-dispatch") openDispatchConfirmation(false);
  if (action === "confirm-dispatch") {
    if (getState().integrations?.composio?.configured && !document.getElementById("dispatch-live-consent")?.checked) {
      toast("Centang persetujuan sebelum mengirim ringkasan ke Composio.", "error");
      return;
    }
    dispatchFollowUp();
  }
  if (action === "open-objection") openObjection();
  if (action === "download-objection") downloadObjectionDocx();
  if (action === "copy-objection") navigator.clipboard.writeText(document.getElementById("objection-draft")?.value || "").then(() => toast("Draf klarifikasi disalin."), () => toast("Clipboard tidak dapat diakses browser.", "error"));
  if (action === "print-objection") window.print();
  if (action === "browse-file") document.querySelector(`[data-file-input="${target.dataset.fileTarget}"]`)?.click();
  if (action === "view-overview") { setState({ activeView: "overview" }); document.querySelector(".main-content")?.scrollTo({ top: 0, behavior: "smooth" }); }
  if (action === "focus-audits") { setState({ activeView: "audits" }); document.getElementById("audit-register")?.scrollIntoView({ behavior: "smooth", block: "start" }); }
  if (action === "focus-review") { setState({ activeView: "review" }); document.getElementById("risk-review")?.scrollIntoView({ behavior: "smooth", block: "start" }); }
  if (action === "review-tab") {
    const tab = target.dataset.tab === "insights" ? "insights" : "matrix";
    setState({ reviewTab: tab, reviewInsightsVisited: getState().reviewInsightsVisited || tab === "insights" });
  }
  if (action === "select-audit") setState({ selectedAuditId: target.dataset.auditId });
  if (action === "review-filter") setState({ reviewFilter: target.dataset.filter, expandedFindingId: null });
  if (action === "toggle-finding") setState({ expandedFindingId: getState().expandedFindingId === target.dataset.findingId ? null : target.dataset.findingId });
  if (action === "record-review-feedback") {
    target.disabled = true;
    try {
      const feedback = await api.recordFindingReview({
        audit_id: target.dataset.auditId,
        finding_id: target.dataset.findingId,
        outcome: target.dataset.outcome,
      });
      setState({ reviewFeedback: feedback });
      toast("Catatan reviewer tersimpan lokal.");
    } catch (error) {
      target.disabled = false;
      toast(error.message, "error");
    }
  }
  if (action === "rerun-audit") openAuditDialog(getState().lastAuditDraft);
});

root.addEventListener("keydown", (event) => {
  const tab = event.target.closest('[role="tab"]');
  if (tab && ["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
    const tabs = [...root.querySelectorAll('[role="tab"]')];
    const currentIndex = tabs.indexOf(tab);
    const nextIndex = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (currentIndex + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    event.preventDefault();
    tabs[nextIndex]?.focus();
    tabs[nextIndex]?.click();
    return;
  }
  const dropZone = event.target.closest(".drop-zone");
  if (dropZone && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    document.querySelector(`[data-file-input="${dropZone.dataset.dropTarget}"]`)?.click();
    return;
  }
  const row = event.target.closest(".audit-row");
  if (row && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    setState({ selectedAuditId: row.dataset.auditId });
  }
  const reviewRow = event.target.closest(".review-row");
  if (reviewRow && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    setState({ expandedFindingId: getState().expandedFindingId === reviewRow.dataset.findingId ? null : reviewRow.dataset.findingId });
  }
});

root.addEventListener("dragover", (event) => {
  const zone = event.target.closest(".drop-zone");
  if (!zone) return;
  event.preventDefault();
  zone.classList.add("is-dragging");
});

root.addEventListener("dragleave", (event) => {
  const zone = event.target.closest(".drop-zone");
  if (zone && !zone.contains(event.relatedTarget)) zone.classList.remove("is-dragging");
});

root.addEventListener("drop", (event) => {
  const zone = event.target.closest(".drop-zone");
  if (!zone) return;
  event.preventDefault();
  zone.classList.remove("is-dragging");
  ingestFiles(event.dataTransfer?.files, zone.dataset.dropTarget);
});

root.addEventListener("input", (event) => {
  if (event.target.id === "audit-search") {
    setState({ query: event.target.value }, { notify: false });
    loadWorkspace({ includeOverview: false, includeHealth: false, includeFeedback: false });
  }
});

root.addEventListener("change", (event) => {
  if (event.target.id === "risk-filter") {
    setState({ riskFilter: event.target.value }, { notify: false });
    loadWorkspace({ includeOverview: false, includeHealth: false, includeFeedback: false });
  }
  const fileInput = event.target.closest("[data-file-input]");
  if (fileInput) {
    ingestFiles(fileInput.files, fileInput.dataset.fileInput);
    fileInput.value = "";
  }
});

root.addEventListener("submit", async (event) => {
  if (event.target.id === "settings-form") {
    event.preventDefault();
    await saveSettings(event.target);
    return;
  }
  if (event.target.id !== "audit-form") return;
  event.preventDefault();
  if (activeUploads) { toast("Tunggu sampai semua file selesai dibaca.", "error"); return; }
  const form = event.target;
  const values = new FormData(form);
  const payload = {
    package_name: String(values.get("package_name") || "").trim(),
    tender_id: String(values.get("tender_id") || "").trim(),
    notice_number: String(values.get("notice_number") || "").trim(),
    pokja_name: String(values.get("pokja_name") || "").trim(),
    company_name: String(values.get("company_name") || "").trim(),
    contract_value_idr: values.get("contract_value_idr") ? Number(values.get("contract_value_idr")) : null,
    dok_pemilihan: String(values.get("dok_pemilihan") || "").trim(),
    adendum: String(values.get("adendum") || "").trim(),
    pustaka: String(values.get("pustaka") || "").trim(),
    contract_draft: String(values.get("contract_draft") || "").trim(),
    baseline_contract: String(values.get("baseline_contract") || "").trim(),
    review_role: String(values.get("review_role") || "procurement"),
    allow_external_processing: values.get("allow_external_processing") === "on",
  };
  if (!payload.dok_pemilihan && !payload.adendum && !payload.pustaka && !payload.contract_draft && !payload.baseline_contract) {
    toast("Masukkan teks atau unggah minimal satu dokumen.", "error");
    return;
  }
  const submit = document.getElementById("submit-audit");
  if (submit) { submit.disabled = true; submit.textContent = "Memeriksa…"; }
  try {
    const result = await api.evaluateAudit(payload);
    const localRow = {
      ...result, tender_id: result.tender_id || result.audit_id.slice(0, 8).toUpperCase(), agency: result.pokja_name || "",
      vendor_name: result.company_name || "", source: "local_audit_log", risk_method: result.risk.method,
      summary: { ...result.summary, findings: result.findings.length },
    };
    document.getElementById("audit-dialog")?.close();
    form.reset();
    clearUploadedFileLabels();
    setState({ query: "", riskFilter: "ALL", lastAuditDraft: payload });
    await loadWorkspace({ preserveSelection: false });
    const otherRows = getState().audits.filter((row) => row.audit_id !== localRow.audit_id);
    setState({
      audits: [localRow, ...otherRows], selectedAuditId: localRow.audit_id,
      customReview: result, reviewFilter: "ALL", expandedFindingId: null, activeView: "review",
      reviewTab: "insights", reviewInsightsVisited: true,
    });
    try { setState({ reviewFeedback: await api.reviewFeedback(result.audit_id) }); }
    catch { setState({ reviewFeedback: null }); }
    document.getElementById("risk-review")?.scrollIntoView({ behavior: "smooth", block: "start" });
    toast(`Evaluasi selesai: ${result.executive_summary?.eligibility || result.verdict}.`);
  } catch (error) {
    toast(error.message, "error");
  } finally {
    const button = document.getElementById("submit-audit");
    if (button && activeUploads === 0) {
      button.disabled = false;
      button.innerHTML = auditSubmitReadyMarkup;
    }
  }
});

loadWorkspace();
