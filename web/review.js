const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const number = (value) => new Intl.NumberFormat("id-ID").format(Number(value || 0));
const rupiah = (value) => `Rp ${number(Math.round(Number(value || 0)))}`;
const riskLabels = { LOW: "Rendah", MEDIUM: "Sedang", HIGH: "Tinggi", CRITICAL: "Kritis" };
const statusLabels = { TERPENUHI: "Terpenuhi", GAP: "Kesenjangan", EXPIRING: "Segera berakhir", SUPERSEDED: "Diubah adendum", REVIEW: "Perlu diperiksa" };
const statusClasses = { TERPENUHI: "status-ok", GAP: "status-gap", EXPIRING: "status-warn", SUPERSEDED: "status-muted", REVIEW: "status-warn" };

function buildReview(state) {
  const result = state.customReview;
  if (!result) return { isCustom: false, findings: [], package_name: "Belum ada evaluasi", verdict: "—", risk_level: "LOW", summary: "Masukkan dokumen tender dan bukti penyedia untuk memulai pemeriksaan." };
  return {
    ...result,
    id: "latest",
    package_name: result.package_name || "Evaluasi dokumen",
    verdict: result.executive_summary?.eligibility || result.verdict || "NEEDS_REVIEW",
    summary: result.executive_summary?.executive_summary || result.review_recommendation || "Periksa setiap temuan terhadap dokumen sumber.",
    findings: result.findings || [],
    risk_level: result.risk_level || "LOW",
    isCustom: true,
  };
}

export function getReviewSnapshot(state) { return buildReview(state); }

function findingMatches(status, filter) {
  if (filter === "ALL") return true;
  if (filter === "NEEDS_REVIEW") return ["GAP", "EXPIRING", "REVIEW"].includes(status);
  return status === filter;
}

function renderFinding(row, state, review) {
  const expanded = state.expandedFindingId === row.id;
  const status = String(row.status || row.severity || "REVIEW").toUpperCase();
  return `
    <tr class="review-row ${expanded ? "review-row-open" : ""}" data-action="toggle-finding" data-finding-id="${escapeHtml(row.id)}" tabindex="0" aria-expanded="${expanded}">
      <td><strong>${escapeHtml(row.id || "TEMUAN")}</strong><small>${escapeHtml(row.category || "Pemeriksaan")}</small></td>
      <td><strong>${escapeHtml(row.clause || row.category || "Temuan")}</strong><small>Sumber: ${escapeHtml(row.source || "Lokator belum tersedia")}</small></td>
      <td><span class="status-pill ${statusClasses[status] || "status-muted"}">${escapeHtml(statusLabels[status] || status)}</span></td>
      <td><span>${escapeHtml(row.evidence || "Tidak ada bukti teks yang cocok. Periksa dokumen sumber.")}</span>${row.evidence_source ? `<small class="evidence-source">Bukti: ${escapeHtml(row.evidence_source)}</small>` : ""}</td>
    </tr>
    ${expanded ? `<tr class="review-expanded"><td colspan="4"><div class="review-expanded-content">${row.requirement_evidence ? `<p><strong>Kutipan ketentuan</strong>${escapeHtml(row.requirement_evidence)}</p>` : ""}<p><strong>Catatan pemeriksaan</strong>${escapeHtml(row.review_note || "Cocokkan fakta dan kutipan dengan dokumen resmi.")}</p>${review.audit_id && state.reviewFeedback?.audit_id === review.audit_id ? `<div class="reviewer-feedback"><strong>Catat hasil pemeriksaan manusia</strong><div class="reviewer-feedback-actions">${[["SUPPORTED", "Didukung bukti"], ["NEEDS_MORE_INFO", "Perlu informasi"], ["NOT_SUPPORTED", "Tidak didukung"]].map(([outcome, label]) => `<button class="review-feedback-button ${state.reviewFeedback?.outcomes?.[row.id]?.outcome === outcome ? "is-selected" : ""}" data-action="record-review-feedback" data-audit-id="${escapeHtml(review.audit_id)}" data-finding-id="${escapeHtml(row.id)}" data-outcome="${outcome}">${label}</button>`).join("")}</div></div>` : ""}</div></td></tr>` : ""}`;
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
  return `<article class="review-tool-card"><p class="eyebrow">HITUNGAN KLAUSUL KONTRAK</p><h3>Simulasi denda keterlambatan</h3><p class="${uncapped ? "penalty-warning" : "penalty-note"}" role="status">${escapeHtml(warning)}</p>${penalty.clause_quote ? `<blockquote>${escapeHtml(penalty.clause_quote)}</blockquote>` : ""}<div class="review-table-wrap"><table class="review-table"><thead><tr><th>TERLAMBAT</th><th>MENURUT KLAUSUL</th><th>PEMBANDING 1‰/HARI</th><th>ILUSTRASI BATAS 5%</th></tr></thead><tbody>${rows}</tbody></table></div><p class="card-footnote">Batas 5% adalah asumsi simulasi, bukan batas maksimum umum dalam Perpres. Verifikasi nilai dasar dan klausul kontrak.</p></article>`;
}

function renderContextual(data) {
  if (!data || data.status !== "success") return `<div class="insights-unavailable"><strong>Ekstraksi konteks tidak tersedia</strong><p>${escapeHtml(data?.message || (data?.status === "not_requested" ? "Aktifkan persetujuan jika kebijakan organisasi mengizinkan pengiriman teks ke AI." : "Periksa konfigurasi provider. Pemeriksaan lokal tetap tersedia."))}</p></div>`;
  const items = data.items || [];
  return `<div class="insight-card"><div class="insight-card-heading"><div><p class="eyebrow">EKSTRAKSI BERBANTU AI · ${escapeHtml(data.provider || "provider")}</p><h3>${escapeHtml(data.scope || "Konteks untuk diperiksa")}</h3></div><span class="insight-status is-ready">KUTIPAN DIVERIFIKASI</span></div>${items.length ? `<ul class="next-action-list">${items.map((item) => `<li><div><strong>${escapeHtml(item.category)}</strong><blockquote>${escapeHtml(item.quote)}</blockquote><small>${escapeHtml(item.source)}</small><p>${escapeHtml(item.summary)}</p></div></li>`).join("")}</ul>` : `<p>Tidak ada kutipan kontekstual yang lolos pemeriksaan substring persis.</p>`}<p class="insight-footnote">Ekstraksi AI bersifat saran; kecocokan kutipan diperiksa secara lokal. Tidak menetapkan kepatuhan atau keputusan tender.</p></div>`;
}

export function renderReview(state) {
  const review = buildReview(state);
  const findings = review.findings || [];
  const filter = state.reviewFilter || "ALL";
  const visible = findings.filter((row) => findingMatches(String(row.status || "REVIEW").toUpperCase(), filter));
  const counts = Object.fromEntries(["TERPENUHI", "GAP", "EXPIRING", "SUPERSEDED", "REVIEW"].map((status) => [status, findings.filter((item) => String(item.status || "REVIEW").toUpperCase() === status).length]));
  const summary = review.executive_summary || {};
  const risk = riskLabels[review.risk_level] || review.risk_level || "Perlu diperiksa";
  const riskClass = String(review.risk_level || "LOW").toLowerCase();
  const status = summary.eligibility || review.verdict || "—";
  const isNoGo = status === "NO-GO";
  const filters = [["ALL", "Semua", findings.length], ["TERPENUHI", "Terpenuhi", counts.TERPENUHI], ["GAP", "Kesenjangan", counts.GAP], ["NEEDS_REVIEW", "Perlu diperiksa", counts.GAP + counts.EXPIRING + counts.REVIEW], ["SUPERSEDED", "Diubah adendum", counts.SUPERSEDED]]
    .map(([value, label, count]) => `<button class="review-filter ${filter === value ? "is-active" : ""}" data-action="review-filter" data-filter="${value}">${label}<span>${number(count)}</span></button>`).join("");
  const result = review.isCustom ? review : {};
  const tabs = `<div class="review-tabs" role="tablist" aria-label="Bagian pemeriksaan"><button class="review-tab ${state.reviewTab !== "insights" ? "is-active" : ""}" role="tab" aria-selected="${state.reviewTab !== "insights"}" data-action="review-tab" data-tab="matrix">Temuan dan bukti</button><button class="review-tab ${state.reviewTab === "insights" ? "is-active" : ""}" role="tab" aria-selected="${state.reviewTab === "insights"}" data-action="review-tab" data-tab="insights">Konteks dan perubahan</button></div>`;
  const body = state.reviewTab === "insights" ? `<div class="insights-grid">${renderContextual(result.contextual_extraction)}${renderAdendum(result)}</div>` : `
    <div class="review-matrix-card"><div class="matrix-heading"><div><p class="eyebrow">MATRIKS KEPATUHAN</p><h3>Persyaratan dan bukti</h3><p>Klik baris untuk melihat kutipan dan catatan pemeriksaan.</p></div><div class="matrix-filters" role="group" aria-label="Filter status">${filters}</div></div><div class="review-table-wrap"><table class="review-table"><thead><tr><th>ID / KATEGORI</th><th>KETENTUAN</th><th>STATUS</th><th>BUKTI PENYEDIA</th></tr></thead><tbody>${visible.length ? visible.map((row) => renderFinding(row, state, review)).join("") : `<tr><td colspan="4" class="review-empty">${review.isCustom ? "Tidak ada temuan pada filter ini." : "Jalankan evaluasi untuk melihat hasil pemeriksaan."}</td></tr>`}</tbody></table></div><div class="review-table-footer"><span>${number(visible.length)} dari ${number(findings.length)} temuan</span><span>${number(counts.GAP)} kesenjangan · ${number(counts.REVIEW)} perlu diperiksa</span></div></div>
    ${renderPenalty(result.penalty_simulation)}${renderAdendum(result)}`;
  return `<section class="review-workspace" id="risk-review" aria-label="Pemeriksaan persyaratan dan bukti">
    <div class="review-heading"><div><p class="eyebrow">HASIL EVALUASI</p><h2>Pemeriksaan dokumen tender</h2><p>Cocokkan kutipan, persyaratan, dan bukti sebelum mengambil keputusan.</p></div><div class="review-heading-actions">${review.isCustom ? `<button class="button button-quiet button-small" data-action="export-review">Ekspor hasil</button><button class="button button-secondary button-small" data-action="open-objection">Buat draf sanggahan</button>` : ""}</div></div>
    <div class="review-summary-card"><div class="review-verdict"><p class="eyebrow">RINGKASAN EKSEKUTIF</p><h3>${escapeHtml(review.package_name)}</h3><p>${escapeHtml(review.tender_id || "")}${review.pokja_name ? ` · ${escapeHtml(review.pokja_name)}` : ""}</p><div class="review-verdict-row"><span class="review-risk risk-${riskClass}">${escapeHtml(risk)}</span><strong class="eligibility-badge ${isNoGo ? "is-no-go" : "is-go"}">${escapeHtml(status)}</strong></div><p class="review-summary-copy">${escapeHtml(review.summary)}</p><small>${escapeHtml(summary.qualification || "Hasil triase berdasarkan teks yang diberikan, bukan penetapan kelayakan.")}</small></div><div class="review-kpis"><div><span>Jumlah temuan</span><strong>${number(findings.length)}</strong></div><div><span>Perlu bukti</span><strong>${number(summary.missing_mandatory_documents || 0)}</strong></div><div><span>Kegagalan administrasi</span><strong>${number(summary.critical_administrative_failures || 0)}</strong></div><div><span>Potensi selisih skenario</span><strong>${summary.potential_financial_exposure_idr ? rupiah(summary.potential_financial_exposure_idr) : "—"}</strong></div></div></div>
    ${tabs}<div class="review-tab-panel">${body}</div><div class="review-tools-grid"><article class="review-tool-card review-action-card"><div><p class="eyebrow">TINDAK LANJUT</p><h3>Siapkan pemeriksaan Pokja</h3><p>Ekspor hasil atau buat draf surat dari kutipan yang cocok persis dengan sumber.</p></div>${review.isCustom ? `<button class="button button-primary button-small" data-action="open-objection">Buat draf sanggahan</button>` : `<button class="button button-primary button-small" data-action="new-audit">Mulai pemeriksaan</button>`}</article></div>
    <p class="review-caveat">Skor dan label membantu triase. Sistem tidak memverifikasi data ke pemerintah, menetapkan kepatuhan, atau memberikan nasihat hukum.</p></section>`;
}

export { escapeHtml };
