const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const number = (value) => new Intl.NumberFormat("id-ID").format(Number(value || 0));
const rupiah = (value) => `Rp ${number(Math.round(Number(value || 0)))}`;
const riskLabels = { LOW: "Rendah", MEDIUM: "Sedang", HIGH: "Tinggi", CRITICAL: "Kritis" };
const statusLabels = { TERPENUHI: "Terpenuhi", GAP: "Kesenjangan", EXPIRING: "Segera berakhir", SUPERSEDED: "Diubah adendum", REVIEW: "Perlu diperiksa" };
const statusClasses = { TERPENUHI: "status-ok", GAP: "status-gap", EXPIRING: "status-warn", SUPERSEDED: "status-muted", REVIEW: "status-warn" };

function buildReview(state) {
  const result = state.currentAudit || state.customReview || (state.audits && state.audits.find((row) => row.audit_id === state.selectedAuditId)) || (state.audits && state.audits[0]) || null;
  if (!result) return { isCustom: false, findings: [], package_name: "Belum ada evaluasi", verdict: "—", risk_level: "LOW", summary: "Masukkan dokumen tender dan bukti penyedia untuk memulai pemeriksaan." };

  const rawFindings = result.findings || [];
  const overrides = state.reviewerOverrides || {};

  // Apply reviewer overrides (Requirement 3.9)
  const findings = rawFindings.map((f) => {
    const ov = overrides[f.id];
    if (ov === "IGNORED") {
      return { ...f, reviewer_status: "IGNORED", reviewer_note: "Diabaikan oleh reviewer (False Positive)" };
    }
    if (ov === "ACCEPTED") {
      return { ...f, reviewer_status: "ACCEPTED", reviewer_note: "Diterima / diverifikasi oleh reviewer" };
    }
    if (ov === "CLARIFY") {
      return { ...f, reviewer_status: "CLARIFY", reviewer_note: "Perlu klarifikasi Pokja" };
    }
    return f;
  });

  // Calculate overridden verdict (Requirement 3.9)
  let effectiveVerdict = result.executive_summary?.eligibility || result.verdict || "NEEDS_REVIEW";
  let summaryText = result.executive_summary?.executive_summary || result.review_recommendation || result.summary?.executive_summary || "Periksa setiap temuan terhadap dokumen sumber.";

  const remainingGaps = findings.filter((f) => f.status === "GAP" && f.reviewer_status !== "IGNORED");
  const hadGapsInitially = rawFindings.some((f) => f.status === "GAP");
  if (hadGapsInitially && remainingGaps.length === 0) {
    effectiveVerdict = "GO";
    summaryText = "GO (Berdasarkan penilaian reviewer manusia: seluruh temuan GAP telah ditandai Diabaikan / False Positive).";
  }

  return {
    ...result,
    id: result.audit_id || "latest",
    package_name: result.package_name || "Evaluasi dokumen",
    verdict: effectiveVerdict,
    summary: summaryText,
    findings: findings,
    raw_findings: rawFindings,
    risk_level: result.risk_level || (typeof result.risk === "object" ? result.risk?.level : result.risk) || "LOW",
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
  const overrides = state.reviewerOverrides || {};
  const currentOverride = overrides[row.id] || "AUTO";

  return `
    <tr class="review-row ${expanded ? "review-row-open" : ""}" data-action="toggle-finding" data-finding-id="${escapeHtml(row.id)}" tabindex="0" aria-expanded="${expanded}">
      <td><strong>${escapeHtml(row.id || "TEMUAN")}</strong><small>${escapeHtml(row.category || "Pemeriksaan")}</small></td>
      <td><strong>${escapeHtml(row.clause || row.category || "Temuan")}</strong><small>Sumber: ${escapeHtml(row.source || "Lokator belum tersedia")}</small></td>
      <td>
        <span class="status-pill ${statusClasses[status] || "status-muted"}">${escapeHtml(statusLabels[status] || status)}</span>
        ${row.reviewer_status ? `<span class="reviewer-status-pill ${row.reviewer_status === 'IGNORED' ? 'pill-ignored' : 'pill-override'}">${row.reviewer_status === 'IGNORED' ? 'Diabaikan' : row.reviewer_status === 'ACCEPTED' ? 'Diterima' : 'Klarifikasi'}</span>` : ""}
      </td>
      <td><span>${escapeHtml(row.evidence || "Tidak ada bukti teks yang cocok. Periksa dokumen sumber.")}</span>${row.evidence_source ? `<small class="evidence-source">Bukti: ${escapeHtml(row.evidence_source)}</small>` : ""}</td>
    </tr>
    ${expanded ? `
      <tr class="review-expanded">
        <td colspan="4">
          <div class="review-expanded-content">
            ${row.requirement_evidence ? `<p><strong>Kutipan ketentuan:</strong> ${escapeHtml(row.requirement_evidence)}</p>` : ""}
            <p><strong>Catatan pemeriksaan:</strong> ${escapeHtml(row.review_note || "Cocokkan fakta dan kutipan dengan dokumen resmi.")}</p>
            <div class="reviewer-override-panel">
              <label class="reviewer-override-label">
                <strong>Penetapan Reviewer:</strong>
                <select class="reviewer-override-select" data-action="set-reviewer-override" data-finding-id="${escapeHtml(row.id)}">
                  <option value="AUTO" ${currentOverride === "AUTO" ? "selected" : ""}>Otomatis Engine (${escapeHtml(statusLabels[status] || status)})</option>
                  <option value="ACCEPTED" ${currentOverride === "ACCEPTED" ? "selected" : ""}>Diterima (Sesuai Aturan)</option>
                  <option value="IGNORED" ${currentOverride === "IGNORED" ? "selected" : ""}>Diabaikan (False Positive)</option>
                  <option value="CLARIFY" ${currentOverride === "CLARIFY" ? "selected" : ""}>Perlu Klarifikasi Pokja</option>
                </select>
              </label>
            </div>
            ${review.audit_id && state.reviewFeedback?.audit_id === review.audit_id ? `
              <div class="reviewer-feedback">
                <strong>Catat hasil pemeriksaan manusia:</strong>
                <div class="reviewer-feedback-actions">
                  ${[["SUPPORTED", "Didukung bukti"], ["NEEDS_MORE_INFO", "Perlu informasi"], ["NOT_SUPPORTED", "Tidak didukung"]].map(([outcome, label]) => `<button class="review-feedback-button ${state.reviewFeedback?.outcomes?.[row.id]?.outcome === outcome ? "is-selected" : ""}" data-action="record-review-feedback" data-audit-id="${escapeHtml(review.audit_id)}" data-finding-id="${escapeHtml(row.id)}" data-outcome="${outcome}">${label}</button>`).join("")}
                </div>
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
  const status = review.verdict || summary.eligibility || "—";
  const isNoGo = status === "NO-GO";
  const isReview = status === "BELUM CUKUP BUKTI" || status === "NEEDS_REVIEW" || status === "REVIEW";
  const isUnread = status === "TIDAK ADA SYARAT TERBACA";
  const badgeClass = isNoGo ? "is-no-go" : isReview ? "is-review" : isUnread ? "is-muted" : "is-go";
  const filters = [["ALL", "Semua", findings.length], ["TERPENUHI", "Terpenuhi", counts.TERPENUHI], ["GAP", "Kesenjangan", counts.GAP], ["NEEDS_REVIEW", "Perlu diperiksa", counts.GAP + counts.EXPIRING + counts.REVIEW], ["SUPERSEDED", "Diubah adendum", counts.SUPERSEDED]]
    .map(([value, label, count]) => `<button class="review-filter ${filter === value ? "is-active" : ""}" data-action="review-filter" data-filter="${value}">${label}<span>${number(count)}</span></button>`).join("");
  const result = review.isCustom ? review : {};
  const tabs = `<div class="review-tabs" role="tablist" aria-label="Bagian pemeriksaan"><button class="review-tab ${state.reviewTab !== "insights" ? "is-active" : ""}" role="tab" aria-selected="${state.reviewTab !== "insights"}" data-action="review-tab" data-tab="matrix">Temuan dan bukti</button><button class="review-tab ${state.reviewTab === "insights" ? "is-active" : ""}" role="tab" aria-selected="${state.reviewTab === "insights"}" data-action="review-tab" data-tab="insights">Konteks dan perubahan</button></div>`;
  const body = state.reviewTab === "insights" ? `<div class="insights-grid">${renderContextual(result.contextual_extraction)}${renderAdendum(result)}</div>` : `
    <div class="review-matrix-card"><div class="matrix-heading"><div><p class="eyebrow">MATRIKS KEPATUHAN</p><h3>Persyaratan dan bukti</h3><p>Klik baris untuk melihat kutipan, catatan, dan mengubah penetapan reviewer.</p></div><div class="matrix-filters" role="group" aria-label="Filter status">${filters}</div></div><div class="review-table-wrap"><table class="review-table"><thead><tr><th>ID / KATEGORI</th><th>KETENTUAN</th><th>STATUS</th><th>BUKTI PENYEDIA</th></tr></thead><tbody>${visible.length ? visible.map((row) => renderFinding(row, state, review)).join("") : `<tr><td colspan="4" class="review-empty">${review.isCustom ? "Tidak ada temuan pada filter ini." : "Jalankan evaluasi untuk melihat hasil pemeriksaan."}</td></tr>`}</tbody></table></div><div class="review-table-footer"><span>${number(visible.length)} dari ${number(findings.length)} temuan</span><span>${number(counts.GAP)} kesenjangan · ${number(counts.REVIEW)} perlu diperiksa</span></div></div>
    ${renderPenalty(result.penalty_simulation)}${renderAdendum(result)}`;
  const hasSource = Boolean(review.has_source_text || review.source_text || state.lastAuditDraft?.dok_pemilihan);
  const disabledObjectionAttr = !hasSource ? 'disabled title="Teks sumber asli tidak tersedia untuk audit ini (sudah kedaluwarsa atau dihapus). Draf sanggahan memerlukan teks sumber asli untuk verifikasi kutipan."' : '';
  const isPokjaMode = (state.userPerspective || "pokja") === "pokja";

  const headingActionButtons = review.isCustom ? `
    <button class="button button-secondary button-small" data-action="add-more-docs" title="Tambah dokumen dan jalankan ulang pemeriksaan">+ Tambah dokumen & jalankan ulang</button>
    <button class="button button-quiet button-small" data-action="export-review">Ekspor hasil (Excel)</button>
    ${isPokjaMode ? `
      <button class="button button-secondary button-small" data-action="export-minutes" title="Buat Draf Berita Acara Hasil Pemilihan (BAHP) resmi">Draf Berita Acara (DOCX)</button>
    ` : `
      <button class="button button-secondary button-small" data-action="open-objection" ${disabledObjectionAttr}>Buat draf sanggahan</button>
    `}
  ` : "";

  const actionCardContent = isPokjaMode ? `
    <div>
      <p class="eyebrow">TINDAK LANJUT POKJA / PANITIA</p>
      <h3>Pemeriksaan & Berita Acara</h3>
      <p>Verifikasi kepatuhan penyedia, anomali harga timpang, dan siapkan draf Berita Acara Hasil Pemilihan (BAHP).</p>
    </div>
    ${review.isCustom ? `
      <button class="button button-primary button-small" data-action="export-minutes">Ekspor Berita Acara (BAHP)</button>
    ` : `
      <button class="button button-primary button-small" data-action="new-audit">Mulai pemeriksaan</button>
    `}
  ` : `
    <div>
      <p class="eyebrow">TINDAK LANJUT PESERTA / VENDOR</p>
      <h3>Uji Kesiapan & Sanggahan</h3>
      <p>Cek kesiapan berkas sebelum submit ke LPSE dan susun draf sanggahan jika terdapat red-flag KAK.</p>
    </div>
    ${review.isCustom ? `
      <button class="button button-primary button-small" data-action="open-objection" ${disabledObjectionAttr}>Buat draf sanggahan</button>
    ` : `
      <button class="button button-primary button-small" data-action="new-audit">Mulai pemeriksaan</button>
    `}
  `;

  return `<section class="review-workspace" id="risk-review" aria-label="Pemeriksaan persyaratan dan bukti">
    <div class="review-heading">
      <div>
        <p class="eyebrow">HASIL EVALUASI <span>·</span> PERSPEKTIF ${isPokjaMode ? "POKJA / AUDITOR" : "VENDOR / PENYEDIA"}</p>
        <h2>Pemeriksaan dokumen tender</h2>
        <p>Cocokkan kutipan, persyaratan, dan bukti sebelum mengambil keputusan.</p>
      </div>
      <div class="review-heading-actions">
        ${headingActionButtons}
      </div>
    </div>
    <div class="review-summary-card"><div class="review-verdict"><p class="eyebrow">RINGKASAN EKSEKUTIF</p><h3>${escapeHtml(review.package_name)}</h3><p>${escapeHtml(review.tender_id || "")}${review.pokja_name ? ` · ${escapeHtml(review.pokja_name)}` : ""}</p><div class="review-verdict-row"><span class="review-risk risk-${riskClass}">${escapeHtml(risk)}</span><strong class="eligibility-badge ${badgeClass}">${escapeHtml(status)}</strong></div><p class="review-summary-copy">${escapeHtml(review.summary)}</p><small>${escapeHtml(summary.qualification || "Hasil triase berdasarkan teks yang diberikan, bukan penetapan kelayakan.")}</small></div><div class="review-kpis"><div><span>Jumlah temuan</span><strong>${number(findings.length)}</strong></div><div><span>Perlu bukti</span><strong>${number(summary.missing_mandatory_documents || 0)}</strong></div><div><span>Kegagalan administrasi</span><strong>${number(summary.critical_administrative_failures || 0)}</strong></div><div><span>Potensi selisih skenario</span><strong>${summary.potential_financial_exposure_idr ? rupiah(summary.potential_financial_exposure_idr) : "—"}</strong></div></div></div>
    ${tabs}<div class="review-tab-panel">${body}</div><div class="review-tools-grid"><article class="review-tool-card review-action-card">${actionCardContent}</article></div>
    <p class="review-caveat">Skor dan label membantu triase. Sistem tidak memverifikasi data ke pemerintah, menetapkan kepatuhan, atau memberikan nasihat hukum.</p></section>`;
}

export { escapeHtml };
