const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const number = (value) => new Intl.NumberFormat("id-ID").format(Number(value || 0));
const rupiah = (value) => `Rp ${number(Math.round(Number(value || 0)))}`;

export const RISK_META = {
  NOT_ASSESSABLE: { label: "Tidak Dapat Dinilai", css: "risk-na", hint: "Dokumen tidak memuat persyaratan yang dikenali. Ini bukan tanda aman." },
  LOW: { label: "Rendah", css: "risk-low", hint: "Persyaratan yang terbaca terpenuhi." },
  MEDIUM: { label: "Sedang", css: "risk-medium", hint: "Ada bukti yang belum lengkap atau kesenjangan berkeparahan sedang." },
  HIGH: { label: "Tinggi", css: "risk-high", hint: "Ada kesenjangan berkeparahan tinggi yang terkonfirmasi teks." },
  CRITICAL: { label: "Kritis", css: "risk-critical", hint: "Ada kesenjangan pada aturan berdampak kritis atau akumulasi kesenjangan tinggi." },
};
const statusLabels = { TERPENUHI: "Terpenuhi", GAP: "Kesenjangan", EXPIRING: "Segera berakhir", SUPERSEDED: "Diubah adendum", REVIEW: "Perlu diperiksa" };
const statusClasses = { TERPENUHI: "status-ok", GAP: "status-gap", EXPIRING: "status-warn", SUPERSEDED: "status-muted", REVIEW: "status-warn" };
const OUTCOMES = [["SUPPORTED", "Didukung bukti"], ["NEEDS_MORE_INFO", "Perlu klarifikasi"], ["NOT_SUPPORTED", "Tidak didukung (false positive)"]];
const KIND_LABELS = {
  input: "Dokumen masuk", pii_redaction: "Redaksi PII", ai_call: "Panggilan AI", ai_validation: "Validasi kutipan AI",
  calculation: "Kalkulasi Python", decision: "Keputusan risiko", document: "Dokumen dihasilkan", guardrail: "Guardrail",
};

export function riskBadge(level, { large = false } = {}) {
  const meta = RISK_META[level] || RISK_META.NOT_ASSESSABLE;
  return `<span class="risk-badge ${meta.css} ${large ? "risk-badge-large" : ""}" title="${escapeHtml(meta.hint)}"><i aria-hidden="true"></i>Risiko ${escapeHtml(meta.label)}</span>`;
}

function buildReview(state) {
  const result = state.currentAudit || state.customReview || (state.audits && state.audits.find((row) => row.audit_id === state.selectedAuditId)) || (state.audits && state.audits[0]) || null;
  if (!result) return { isCustom: false, findings: [], package_name: "Belum ada evaluasi", verdict: "—", risk_level: "NOT_ASSESSABLE", summary: "Masukkan dokumen tender dan bukti penyedia untuk memulai pemeriksaan." };

  const feedback = state.reviewFeedback?.audit_id === result.audit_id ? state.reviewFeedback : null;
  const outcomes = feedback?.outcomes || {};
  const findings = (result.findings || []).map((finding) => {
    const outcome = outcomes[finding.id]?.outcome;
    return outcome ? { ...finding, reviewer_outcome: outcome } : finding;
  });
  const reviewed = feedback?.reviewed_assessment;
  const excluded = reviewed?.excluded_by_reviewer || [];
  const risk = reviewed && excluded.length ? reviewed : (result.risk || {});
  return {
    ...result,
    id: result.audit_id || "latest",
    package_name: result.package_name || "Evaluasi dokumen",
    verdict: reviewed && excluded.length ? reviewed.verdict : (result.executive_summary?.eligibility || result.verdict || "—"),
    system_verdict: result.executive_summary?.eligibility || result.verdict,
    reviewed_by_human: Boolean(reviewed && excluded.length),
    summary: result.executive_summary?.executive_summary || result.review_recommendation || "Periksa setiap temuan terhadap dokumen sumber.",
    findings,
    risk,
    risk_level: risk.level || result.risk_level || "NOT_ASSESSABLE",
    isCustom: true,
  };
}

export function getReviewSnapshot(state) { return buildReview(state); }

function findingMatches(status, filter) {
  if (filter === "ALL") return true;
  if (filter === "NEEDS_REVIEW") return ["GAP", "EXPIRING", "REVIEW"].includes(status);
  return status === filter;
}

function renderFinding(row, state, review, role) {
  const expanded = state.expandedFindingId === row.id;
  const status = String(row.status || "REVIEW").toUpperCase();
  const outcome = row.reviewer_outcome;
  const outcomeLabel = OUTCOMES.find(([value]) => value === outcome)?.[1];
  const tags = [
    row.origin === "ai_extraction_python_validated" ? '<span class="tag tag-ai">Diekstrak AI · divalidasi Python</span>' : "",
    role === "vendor" && row.objectionable ? '<span class="tag tag-objection">Dapat disanggah</span>' : "",
    role === "vendor" && row.party === "bidder_evidence" && status !== "TERPENUHI" ? '<span class="tag tag-homework">Lengkapi berkas Anda</span>' : "",
    outcomeLabel ? `<span class="tag ${outcome === "NOT_SUPPORTED" ? "tag-ignored" : "tag-reviewed"}">Reviewer: ${escapeHtml(outcomeLabel)}</span>` : "",
  ].join("");
  return `
    <tr class="review-row ${expanded ? "review-row-open" : ""} ${outcome === "NOT_SUPPORTED" ? "is-dismissed" : ""}" data-action="toggle-finding" data-finding-id="${escapeHtml(row.id)}" tabindex="0" aria-expanded="${expanded}">
      <td><strong>${escapeHtml(row.id || "TEMUAN")}</strong><small>${escapeHtml(row.category || "Pemeriksaan")}</small></td>
      <td><strong>${escapeHtml(row.clause || row.category || "Temuan")}</strong><small>Sumber: ${escapeHtml(row.source || "Lokator belum tersedia")}</small><div class="tag-row">${tags}</div></td>
      <td><span class="status-pill ${statusClasses[status] || "status-muted"}">${escapeHtml(statusLabels[status] || status)}</span></td>
      <td><span>${escapeHtml(row.evidence || "Tidak ada bukti teks yang cocok. Periksa dokumen sumber.")}</span>${row.evidence_source ? `<small class="evidence-source">Bukti: ${escapeHtml(row.evidence_source)}</small>` : ""}</td>
    </tr>
    ${expanded ? `
      <tr class="review-expanded">
        <td colspan="4">
          <div class="review-expanded-content">
            ${row.requirement_evidence ? `<p><strong>Kutipan ketentuan (verbatim):</strong> ${escapeHtml(row.requirement_evidence)}</p>` : ""}
            <p><strong>Catatan pemeriksaan:</strong> ${escapeHtml(row.review_note || "Cocokkan fakta dan kutipan dengan dokumen resmi.")}</p>
            ${row.legal_reference ? `<p class="legal-ref"><strong>Rujukan kandidat:</strong> ${escapeHtml(row.legal_reference)} <span class="tag tag-legal">Perlu verifikasi hukum</span></p>` : ""}
            ${row.calculation_ref ? `<p><button type="button" class="button button-quiet button-small" data-action="open-proof-step" data-step-id="${escapeHtml(row.calculation_ref)}">Lihat hitungan Python (${escapeHtml(row.calculation_ref)})</button></p>` : ""}
            ${review.audit_id ? `
              <div class="reviewer-feedback">
                <strong>Keputusan reviewer manusia (tersimpan di log audit):</strong>
                <div class="reviewer-feedback-actions">
                  ${OUTCOMES.map(([value, label]) => `<button type="button" class="review-feedback-button ${outcome === value ? "is-selected" : ""}" data-action="record-review-feedback" data-audit-id="${escapeHtml(review.audit_id)}" data-finding-id="${escapeHtml(row.id)}" data-outcome="${value}">${label}</button>`).join("")}
                </div>
                <small>Temuan "tidak didukung" dikeluarkan dari perhitungan risiko pasca-review, BA, dan sanggahan.</small>
              </div>` : ""}
          </div>
        </td>
      </tr>` : ""}`;
}

function renderAdendum(result) {
  const diff = result.adendum_reconciliation;
  if (!diff || diff.status !== "compared") return "";
  const rows = (diff.changes || []).map((item) => `<tr><td>${escapeHtml(item.item_id)}</td><td>${escapeHtml(item.change_status)}</td><td>${escapeHtml(item.original_requirement || "—")}</td><td>${escapeHtml(item.adendum_requirement || "—")}</td></tr>`).join("");
  return `<article class="review-tool-card"><p class="eyebrow">REKONSILIASI ADENDUM</p><h3>Perubahan persyaratan</h3><p>${escapeHtml(diff.review_note || "Perubahan teks perlu diperiksa.")}</p><div class="review-table-wrap"><table class="review-table"><thead><tr><th>ID</th><th>STATUS</th><th>TEKS ASLI</th><th>TEKS ADENDUM</th></tr></thead><tbody>${rows || '<tr><td colspan="4">Tidak ada perubahan teks yang terdeteksi.</td></tr>'}</tbody></table></div></article>`;
}

function renderPenalty(penalty) {
  if (!penalty || penalty.status === "contract_value_required") return "";
  const rows = (penalty.scenarios || []).map((item) => `<tr><td>${number(item.delay_days)} hari</td><td>${rupiah(item.contract_clause_amount_idr)}</td><td>${rupiah(item["1_per_mille_daily_comparison_idr"])}</td><td>${rupiah(item.illustrative_5_percent_cap_amount_idr)}</td></tr>`).join("");
  const uncapped = (penalty.alerts || []).includes("CRITICAL_POISON_PILL");
  const warning = uncapped ? "Klausul denda tanpa batas maksimum terdeteksi. Minta penelaahan sebelum penawaran." : "Perhitungan mengikuti teks klausul yang terbaca.";
  return `<article class="review-tool-card"><p class="eyebrow">KALKULATOR PYTHON · DENDA KETERLAMBATAN</p><h3>Simulasi denda keterlambatan</h3><p class="formula">denda = nilai kontrak × tarif harian × hari terlambat</p><p class="${uncapped ? "penalty-warning" : "penalty-note"}" role="status">${escapeHtml(warning)}</p>${penalty.clause_quote ? `<blockquote>${escapeHtml(penalty.clause_quote)}</blockquote>` : ""}<div class="review-table-wrap"><table class="review-table"><thead><tr><th>TERLAMBAT</th><th>MENURUT KLAUSUL</th><th>PEMBANDING 1‰/HARI</th><th>ILUSTRASI BATAS 5%</th></tr></thead><tbody>${rows}</tbody></table></div><p class="card-footnote">Batas 5% adalah asumsi simulasi, bukan batas maksimum umum dalam Perpres. Verifikasi nilai dasar dan klausul kontrak.</p></article>`;
}

function renderContextual(data) {
  if (!data || data.status !== "success") return `<div class="insights-unavailable"><strong>Ekstraksi AI tidak dijalankan</strong><p>${escapeHtml(data?.message || (data?.status === "not_requested" ? "Aktifkan persetujuan jika kebijakan organisasi mengizinkan pengiriman teks ke AI." : "Periksa konfigurasi provider. Pemeriksaan lokal tetap tersedia."))}</p></div>`;
  const items = data.items || [];
  const validationLabel = { confirmed: "Dikonfirmasi Python → temuan", corroborated: "Sama dengan temuan lokal", not_confirmed: "Tidak lolos validasi Python", context_only: "Konteks saja" };
  return `<div class="insight-card"><div class="insight-card-heading"><div><p class="eyebrow">EKSTRAKSI AI · ${escapeHtml(data.provider || "provider")} ${data.model_id ? `· ${escapeHtml(data.model_id)}` : ""}</p><h3>${escapeHtml(data.scope || "Kutipan yang diekstrak model")}</h3></div><span class="insight-status is-ready">${number(items.length)} KUTIPAN DIVERIFIKASI · ${number(data.rejected_quotes_count || 0)} DITOLAK</span></div>${items.length ? `<ul class="next-action-list">${items.map((item) => `<li><div><strong>${escapeHtml(item.category)}</strong> <span class="tag ${item.validation?.status === "confirmed" ? "tag-ai" : "tag-muted"}">${escapeHtml(validationLabel[item.validation?.status] || "—")}</span><blockquote>${escapeHtml(item.quote)}</blockquote><small>${escapeHtml(item.source)}</small><p>${escapeHtml(item.validation?.detail || item.summary)}</p></div></li>`).join("")}</ul>` : `<p>Tidak ada kutipan yang lolos pemeriksaan substring persis.</p>`}<p class="insight-footnote">Model hanya mengekstrak kutipan. Setiap kutipan dicek substring-persis terhadap dokumen, lalu divalidasi ulang oleh aturan Python sebelum boleh memengaruhi verdict.</p></div>`;
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") return Number.isInteger(value) && Math.abs(value) >= 1000 ? number(value) : String(value);
  if (typeof value === "boolean") return value ? "ya" : "tidak";
  if (Array.isArray(value)) return value.length ? value.map(formatValue).join(", ") : "—";
  if (typeof value === "object") return Object.entries(value).map(([key, item]) => `${key}: ${formatValue(item)}`).join(" · ");
  return String(value);
}

function renderKeyValues(object) {
  const entries = Object.entries(object || {});
  if (!entries.length) return "";
  return `<dl class="proof-kv">${entries.map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(formatValue(value))}</dd></div>`).join("")}</dl>`;
}

export function renderProof(state, review) {
  if (state.proofLoading) return '<div class="proof-empty">Memuat jejak audit…</div>';
  const proof = state.proof && state.proof.audit_id === review.audit_id ? state.proof : null;
  const steps = proof?.steps || review.proof_log || [];
  if (!steps.length) return '<div class="proof-empty"><strong>Jejak audit belum tersedia untuk audit ini.</strong><p>Audit lama (sebelum pembaruan) tidak menyimpan jejak. Jalankan ulang evaluasi.</p></div>';
  const summary = proof?.summary || review.proof_summary || {};
  const table = proof?.decision_table || [];
  const ai = proof?.ai_governance || review.ai_governance_metadata || {};
  const documents = proof?.documents || review.documents || [];
  const focus = state.proofFocus;
  return `
    <div class="proof-header">
      <div class="proof-stats">
        <div><span>Langkah tercatat</span><strong>${number(summary.steps || steps.length)}</strong></div>
        <div><span>Panggilan AI berhasil</span><strong>${number(summary.ai_calls || 0)}</strong><small>${escapeHtml((summary.ai_providers || []).join(", ") || "tidak ada")}</small></div>
        <div><span>Kalkulasi Python</span><strong>${number(summary.python_calculations || 0)}</strong></div>
        <div><span>Provider yang benar-benar dipakai</span><strong>${escapeHtml(ai.provider_used || "Tidak ada (aturan lokal)")}</strong><small>${escapeHtml(ai.model_used || ai.role_of_ai || "")}</small></div>
      </div>
      <p class="proof-lede">Urutan bukti: <b>dokumen</b> → <b>redaksi PII</b> → <b>ekstraksi AI (opsional)</b> → <b>validasi kutipan</b> → <b>kalkulasi Python</b> → <b>tabel keputusan</b> → <b>dokumen hasil</b>. Teks dokumen tidak disimpan di jejak ini; hanya hash, angka, dan kutipan pendek.</p>
    </div>
    <ol class="proof-timeline">
      ${steps.map((step) => `
        <li id="proof-${escapeHtml(step.step_id)}" class="proof-step proof-${escapeHtml(step.kind)} proof-status-${escapeHtml(step.status)} ${focus === step.step_id ? "is-focused" : ""}">
          <div class="proof-step-head">
            <span class="proof-id">${escapeHtml(step.step_id)}</span>
            <span class="proof-kind">${escapeHtml(KIND_LABELS[step.kind] || step.kind)}</span>
            <strong>${escapeHtml(step.title)}</strong>
            <span class="proof-actor">${escapeHtml(step.actor)}</span>
            ${step.duration_ms != null ? `<span class="proof-time">${number(step.duration_ms)} ms</span>` : ""}
            <span class="proof-status">${escapeHtml({ ok: "OK", skipped: "Dilewati", failed: "Gagal", rejected: "Ada yang ditolak" }[step.status] || step.status)}</span>
          </div>
          ${step.formula ? `<p class="formula">${escapeHtml(step.formula)}</p>` : ""}
          <div class="proof-io">
            ${Object.keys(step.inputs || {}).length ? `<div><h4>Input</h4>${renderKeyValues(step.inputs)}</div>` : ""}
            ${Object.keys(step.outputs || {}).length ? `<div><h4>Output</h4>${renderKeyValues(step.outputs)}</div>` : ""}
          </div>
          ${step.note ? `<p class="proof-note">${escapeHtml(step.note)}</p>` : ""}
        </li>`).join("")}
      ${documents.map((doc) => `
        <li class="proof-step proof-document">
          <div class="proof-step-head"><span class="proof-id">DOC</span><span class="proof-kind">Dokumen dihasilkan</span><strong>${escapeHtml(doc.filename)}</strong><span class="proof-actor">peran: ${escapeHtml(doc.role || "—")}</span><span class="proof-status">OK</span></div>
          ${renderKeyValues({ sha256: doc.sha256, temuan_dimasukkan: doc.findings_included, dibuat: doc.created_at })}
        </li>`).join("")}
    </ol>
    ${table.length ? `<article class="review-tool-card"><p class="eyebrow">TABEL KEPUTUSAN RISIKO (DETERMINISTIK)</p><h3>Aturan yang dipakai: ${escapeHtml(review.risk?.rule_applied || "—")}</h3><table class="review-table decision-table"><thead><tr><th>ATURAN</th><th>KONDISI</th><th>TINGKAT</th></tr></thead><tbody>${table.map((rule) => `<tr class="${rule.rule === review.risk?.rule_applied ? "is-applied" : ""}"><td>${escapeHtml(rule.rule)}</td><td>${escapeHtml(rule.condition)}</td><td>${riskBadge(rule.level)}</td></tr>`).join("")}</tbody></table></article>` : ""}`;
}

function roleActions(review, role, hasSource) {
  if (!review.isCustom) return '<button class="button button-primary" data-action="new-audit">Mulai pemeriksaan</button>';
  const boq = '<button class="button button-secondary" data-action="export-boq">Unduh BoQ (.xlsx)</button>';
  if (role === "pokja") {
    return `
      <button class="button button-primary" data-action="export-minutes">Draf Berita Acara (.docx)</button>
      <button class="button button-secondary" data-action="export-clarification">Surat klarifikasi ke penyedia (.docx)</button>
      ${boq}`;
  }
  const objectionable = (review.findings || []).filter((item) => item.objectionable && item.reviewer_outcome !== "NOT_SUPPORTED").length;
  return `
    <button class="button button-primary" data-action="open-objection" ${!hasSource || !objectionable ? "disabled" : ""} title="${objectionable ? "" : "Tidak ada kesenjangan dokumen tender yang dapat disanggah"}">Draf sanggahan (.docx) · ${number(objectionable)} poin</button>
    ${boq}`;
}

export function renderReview(state) {
  const role = state.session?.role || "pokja";
  const review = buildReview(state);
  const findings = review.findings || [];
  const filter = state.reviewFilter || "ALL";
  const visible = findings.filter((row) => findingMatches(String(row.status || "REVIEW").toUpperCase(), filter));
  const counts = Object.fromEntries(["TERPENUHI", "GAP", "EXPIRING", "SUPERSEDED", "REVIEW"].map((status) => [status, findings.filter((item) => String(item.status || "REVIEW").toUpperCase() === status).length]));
  const summary = review.executive_summary || {};
  const status = review.verdict || "—";
  const badgeClass = status === "NO-GO" ? "is-no-go" : status === "BELUM CUKUP BUKTI" ? "is-review" : status === "TIDAK ADA SYARAT TERBACA" ? "is-muted" : "is-go";
  const filters = [["ALL", "Semua", findings.length], ["TERPENUHI", "Terpenuhi", counts.TERPENUHI], ["GAP", "Kesenjangan", counts.GAP], ["NEEDS_REVIEW", "Perlu diperiksa", counts.GAP + counts.EXPIRING + counts.REVIEW], ["SUPERSEDED", "Diubah adendum", counts.SUPERSEDED]]
    .map(([value, label, count]) => `<button class="review-filter ${filter === value ? "is-active" : ""}" data-action="review-filter" data-filter="${value}">${label}<span>${number(count)}</span></button>`).join("");
  const tab = state.reviewTab || "matrix";
  const tabs = `<div class="review-tabs" role="tablist" aria-label="Bagian pemeriksaan">
    ${[["matrix", "Temuan dan bukti"], ["proof", "Jejak audit: AI → Python → keputusan"], ["insights", "Ekstraksi AI dan adendum"]].map(([key, label]) => `<button class="review-tab ${tab === key ? "is-active" : ""}" role="tab" aria-selected="${tab === key}" data-action="review-tab" data-tab="${key}">${label}</button>`).join("")}
  </div>`;
  let body;
  if (tab === "insights") body = `<div class="insights-grid">${renderContextual(review.isCustom ? review.contextual_extraction : null)}${renderAdendum(review)}</div>`;
  else if (tab === "proof") body = renderProof(state, review);
  else body = `
    <div class="review-matrix-card"><div class="matrix-heading"><div><p class="eyebrow">MATRIKS PERSYARATAN</p><h3>Persyaratan dan bukti</h3><p>Klik baris untuk melihat kutipan verbatim, rujukan kandidat, hitungan Python, dan mencatat keputusan reviewer.</p></div><div class="matrix-filters" role="group" aria-label="Filter status">${filters}</div></div><div class="review-table-wrap"><table class="review-table"><thead><tr><th>ID / KATEGORI</th><th>KETENTUAN</th><th>STATUS</th><th>BUKTI PENYEDIA</th></tr></thead><tbody>${visible.length ? visible.map((row) => renderFinding(row, state, review, role)).join("") : `<tr><td colspan="4" class="review-empty">${review.isCustom ? "Tidak ada temuan pada filter ini." : "Jalankan evaluasi untuk melihat hasil pemeriksaan."}</td></tr>`}</tbody></table></div><div class="review-table-footer"><span>${number(visible.length)} dari ${number(findings.length)} temuan</span><span>${number(counts.GAP)} kesenjangan · ${number(counts.REVIEW)} perlu diperiksa</span></div></div>
    ${renderPenalty(review.isCustom ? review.penalty_simulation : null)}`;
  const hasSource = Boolean(review.has_source_text || review.source_text);
  const risk = review.risk || {};
  const riskMeta = RISK_META[review.risk_level] || RISK_META.NOT_ASSESSABLE;
  const roleCopy = role === "pokja"
    ? { eyebrow: "RUANG KERJA POKJA PEMILIHAN", title: "Evaluasi dokumen & Berita Acara", text: "Periksa kesenjangan, catat keputusan reviewer, lalu unduh draf Berita Acara dan BoQ." }
    : { eyebrow: "RUANG KERJA PENYEDIA / VENDOR", title: "Kesiapan penawaran & sanggahan", text: "Lengkapi berkas Anda sendiri, lalu susun sanggahan hanya untuk kesenjangan pada dokumen tender." };

  return `<section class="review-workspace" id="risk-review" aria-label="Pemeriksaan persyaratan dan bukti">
    <div class="review-heading">
      <div>
        <p class="eyebrow">${roleCopy.eyebrow}</p>
        <h2>${roleCopy.title}</h2>
        <p>${roleCopy.text}</p>
      </div>
      <div class="review-heading-actions">
        ${review.isCustom ? '<button class="button button-quiet" data-action="add-more-docs">+ Tambah dokumen & jalankan ulang</button>' : ""}
      </div>
    </div>
    <div class="risk-hero ${riskMeta.css}">
      <div class="risk-hero-main">
        <p class="eyebrow">TINGKAT RISIKO ${review.reviewed_by_human ? "· SETELAH REVIEW MANUSIA" : "· HASIL ATURAN DETERMINISTIK"}</p>
        <div class="risk-hero-title">${riskBadge(review.risk_level, { large: true })}<strong class="eligibility-badge ${badgeClass}">${escapeHtml(status)}</strong></div>
        <h3>${escapeHtml(review.package_name)}</h3>
        <p class="risk-rationale">${escapeHtml(risk.rationale || riskMeta.hint)}</p>
        <p class="risk-rule">Aturan ${escapeHtml(risk.rule_applied || "—")} dari tabel keputusan · <button type="button" class="link-button" data-action="review-tab" data-tab="proof">lihat jejak audit</button>${review.reviewed_by_human ? ` · verdict sistem semula: <b>${escapeHtml(review.system_verdict)}</b>` : ""}</p>
        <p class="review-summary-copy">${escapeHtml(review.summary)}</p>
      </div>
      <div class="review-kpis">
        <div><span>Kesenjangan</span><strong>${number(counts.GAP)}</strong></div>
        <div><span>Perlu bukti</span><strong>${number(counts.REVIEW + counts.EXPIRING)}</strong></div>
        <div><span>Terpenuhi</span><strong>${number(counts.TERPENUHI)}</strong></div>
        <div><span>Selisih skenario denda</span><strong>${summary.potential_financial_exposure_idr ? rupiah(summary.potential_financial_exposure_idr) : "—"}</strong></div>
      </div>
    </div>
    <div class="role-action-bar" aria-label="Tindak lanjut">${roleActions(review, role, hasSource)}</div>
    ${tabs}<div class="review-tab-panel">${body}</div>
    <p class="review-caveat">Tingkat risiko adalah hasil tabel keputusan atas teks yang diberikan. Sistem tidak memverifikasi data ke instansi pemerintah, tidak menetapkan kepatuhan, dan tidak memberi nasihat hukum; setiap draf wajib ditinjau manusia.</p></section>`;
}

export { escapeHtml };
