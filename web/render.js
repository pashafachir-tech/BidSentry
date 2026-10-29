import { renderReview } from "./review.js?v=2.2.0";

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const number = (value) => new Intl.NumberFormat("id-ID").format(Number(value || 0));
const rupiah = (value) => `Rp ${number(value)}`;

const riskMeta = {
  LOW: { label: "Rendah", css: "risk-low" },
  MEDIUM: { label: "Sedang", css: "risk-medium" },
  HIGH: { label: "Tinggi", css: "risk-high" },
  CRITICAL: { label: "Kritis", css: "risk-critical" },
};

function icon(name) {
  const paths = {
    overview: '<rect x="3" y="3" width="7" height="7" rx="1.4"/><rect x="14" y="3" width="7" height="7" rx="1.4"/><rect x="3" y="14" width="7" height="7" rx="1.4"/><rect x="14" y="14" width="7" height="7" rx="1.4"/>',
    audit: '<path d="M8 3h8l4 4v14H4V3h4Z"/><path d="M14 3v5h6M8 13h8M8 17h5"/>',
    shield: '<path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5M12 15V3"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    refresh: '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.6 9A7 7 0 0 1 17 6l3 6M4 12l3 6a7 7 0 0 0 11.4-3"/>',
    close: '<path d="m18 6-12 12M6 6l12 12"/>',
    file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    folder: '<path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/>',
    layers: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    alert: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    check: '<polyline points="20 6 9 17 4 12"/>',
  };
  return `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">${paths[name] || paths.audit}</svg>`;
}

function badge(level) {
  const meta = riskMeta[level] || riskMeta.MEDIUM;
  return `<span class="risk-badge ${meta.css}"><i></i>${meta.label}</span>`;
}

function statusPill(status) {
  const css = { TERPENUHI: "status-ok", GAP: "status-gap", EXPIRING: "status-warn", SUPERSEDED: "status-muted", REVIEW: "status-warn", HIGH: "status-gap", CRITICAL: "status-gap", MEDIUM: "status-warn", LOW: "status-ok" }[status] || "status-muted";
  const label = { TERPENUHI: "Terpenuhi", GAP: "Kesenjangan", EXPIRING: "Segera berakhir", SUPERSEDED: "Diubah adendum", REVIEW: "Perlu diperiksa", HIGH: "Tinggi", CRITICAL: "Kritis", MEDIUM: "Sedang", LOW: "Rendah" }[status] || status || "Perlu diperiksa";
  return `<span class="status-pill ${css}">${escapeHtml(label)}</span>`;
}

function rowsMarkup(rows, selectedId) {
  if (!rows || !rows.length) return '<tr><td colspan="5" class="empty-row">Belum ada audit tersimpan atau tidak ada yang cocok dengan pencarian.</td></tr>';
  return rows.map((row) => `
    <tr class="audit-row ${row.audit_id === selectedId ? "is-selected" : ""}" data-action="select-audit" data-audit-id="${escapeHtml(row.audit_id)}" tabindex="0" aria-label="Lihat audit ${escapeHtml(row.package_name)}">
      <td><div class="package-cell"><span class="package-dot ${riskMeta[row.risk_level]?.css || "risk-medium"}"></span><span><strong>${escapeHtml(row.package_name)}</strong><small>${escapeHtml(row.tender_id || row.audit_id)} · ${escapeHtml(row.agency || "Workspace lokal")}</small></span></div></td>
      <td>${escapeHtml(row.vendor_name || "—")}</td><td class="amount-cell">${row.contract_value_idr ? rupiah(row.contract_value_idr) : "—"}</td>
      <td>${badge(row.risk_level)}</td><td><div class="score-row-wrapper"><span class="score-cell">${number(row.risk_score)}<small>/100</small></span><button type="button" class="row-delete-action" data-action="delete-audit" data-audit-id="${escapeHtml(row.audit_id)}" data-package-name="${escapeHtml(row.package_name)}" title="Hapus pemeriksaan ${escapeHtml(row.package_name)}" aria-label="Hapus pemeriksaan ${escapeHtml(row.package_name)}"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"/></svg></button></div></td>
    </tr>`).join("");
}

function detailMarkup(row) {
  if (!row) return `<section class="detail-card"><div class="detail-empty"><span class="detail-empty-icon">${icon("audit")}</span><h2>Pilih paket untuk ditinjau</h2><p>Pilih satu baris audit untuk melihat ringkasan risiko dan bukti.</p></div></section>`;
  const findings = row.findings || [];
  const findingCount = findings.length || row.summary?.findings || row.summary?.total || 0;
  const preview = findings.slice(0, 4);
  const levelClass = riskMeta[row.risk_level]?.css || "risk-medium";
  const sourceLabel = "Audit lokal";
  return `
    <section class="detail-card" aria-label="Rincian audit terpilih">
      <div class="detail-head"><div><p class="eyebrow">ANALISIS PAKET</p><h2>${escapeHtml(row.package_name)}</h2><p class="detail-subtitle">${escapeHtml(row.tender_id || row.audit_id)} · ${escapeHtml(row.agency || "Workspace lokal")}</p></div><button type="button" class="icon-button-danger" data-action="delete-audit" data-audit-id="${escapeHtml(row.audit_id)}" data-package-name="${escapeHtml(row.package_name)}" title="Hapus pemeriksaan ${escapeHtml(row.package_name)} dari riwayat" aria-label="Hapus riwayat"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:15px;height:15px"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"/></svg></button></div>
      <div class="score-panel"><div class="score-ring ${levelClass}" style="--score:${Math.max(0, Math.min(100, Number(row.risk_score || 0)))}"><div><strong>${number(row.risk_score)}</strong><small>/100</small></div></div><div><span class="eyebrow">INDEKS TRIAGE</span>${badge(row.risk_level)}<p>Indeks aturan untuk membantu prioritas review, bukan probabilitas fraud. Skor 0 berarti tidak ada pemicu berbobot yang terdeteksi; bukan bukti paket bebas risiko.</p></div></div>
      <div class="detail-stats"><div><span>Temuan</span><strong>${number(findings.length || row.summary?.findings || 0)}</strong></div><div><span>Nilai kontrak</span><strong>${row.contract_value_idr ? rupiah(row.contract_value_idr) : "—"}</strong></div><div><span>Sumber</span><strong>${sourceLabel}</strong></div></div>
      <div class="finding-heading"><h3>Temuan untuk ditinjau</h3><span>${number(findingCount)} total</span></div>
      <div class="finding-list">${preview.length ? preview.map((finding) => `<article class="finding-item"><div class="finding-mark ${["CRITICAL", "HIGH"].includes(finding.severity) ? "mark-high" : "mark-low"}"></div><div><div class="finding-title-row"><strong>${escapeHtml(finding.clause || finding.category || "Temuan")}</strong>${statusPill(finding.status || finding.severity)}</div><p>${escapeHtml(finding.evidence || finding.review_note || "Periksa sumber dokumen.")}</p><small>${escapeHtml(finding.source || "Sumber belum ditentukan")}</small></div></article>`).join("") : findingCount ? '<div class="no-findings">Log menyimpan jumlah dan status temuan, bukan kutipan dokumen. Buka sumber asli untuk pemeriksaan bukti.</div>' : '<div class="no-findings">Belum ada temuan yang disimpan pada audit ini.</div>'}</div>
      <div class="detail-actions"><button class="button button-secondary button-small" data-action="dispatch-selected">Siapkan tindak lanjut ${icon("arrow")}</button><button class="button button-quiet button-small" data-action="export-selected-review" aria-label="Ekspor Risk Review paket ini ke Excel">Ekspor Risk Review ${icon("download")}</button><button class="button button-quiet button-small text-danger detail-delete-btn" data-action="delete-audit" data-audit-id="${escapeHtml(row.audit_id)}" data-package-name="${escapeHtml(row.package_name)}" title="Hapus pemeriksaan ini dari riwayat"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px;margin-right:4px"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"/></svg>Hapus riwayat</button></div>
      <p class="detail-caveat">Hasil tersimpan tanpa teks dokumen. Periksa kembali sumber asli sebelum mengambil keputusan.</p>
    </section>`;
}

function integrationCopy(integrations) {
  if (!integrations) return "Memeriksa koneksi";
  if (integrations.langflow?.configured) return "Langflow opt-in tersedia";
  return "Audit lokal aktif · Langflow opsional";
}

function renderCrossDocumentSummary(state, selected, allAudits = []) {
  const summaryTab = state.crossSummaryTab || "project";
  const project = selected || state.currentAudit || state.customReview || allAudits[0] || null;

  return `
    <section class="cross-summary-section" id="cross-document-summary" aria-label="Sintesis Forensik Lintas-Dokumen">
      <div class="cross-summary-header">
        <div class="cross-summary-header-main">
          <div class="cross-summary-eyebrow">
            ${icon("layers")}
            <span>INTELIJEN LINTAS-DOKUMEN · SINTESIS FORENSIK BERKAS PROYEK</span>
          </div>
          <h2>Korelasi &amp; Rekonsiliasi Dokumen Tender</h2>
          <p class="cross-summary-desc">
            Sintesis keterhubungan, celah hukum, dan ketidaksinkronan antara KAK (Spesifikasi Teknis), HPS &amp; BoQ, Dokumen Penawaran Rekanan, Adendum BAPP, serta Draf Kontrak (SPK).
          </p>
        </div>
        <div class="cross-summary-tabs" role="tablist" aria-label="Pilihan tampilan sintesis">
          <button type="button" class="cross-tab-btn ${summaryTab === "project" ? "is-active" : ""}" data-action="set-summary-tab" data-tab="project" role="tab" aria-selected="${summaryTab === "project"}">
            ${icon("file")}
            <span>Proyek Terpilih (${project ? escapeHtml(project.package_name) : "Tidak ada"})</span>
          </button>
          <button type="button" class="cross-tab-btn ${summaryTab === "portfolio" ? "is-active" : ""}" data-action="set-summary-tab" data-tab="portfolio" role="tab" aria-selected="${summaryTab === "portfolio"}">
            ${icon("layers")}
            <span>Portofolio Lintas-Proyek (${number(allAudits.length)} Paket)</span>
          </button>
        </div>
      </div>

      ${summaryTab === "portfolio" 
        ? renderPortfolioSummary(allAudits, state)
        : renderProjectCrossSummary(project, state)}
    </section>
  `;
}

function renderProjectCrossSummary(project, state) {
  if (!project) {
    return `
      <div class="cross-summary-empty">
        <span class="cross-empty-icon">${icon("layers")}</span>
        <h3>Belum ada proyek yang dipilih</h3>
        <p>Pilih salah satu folder proyek di bilah kiri atau baris riwayat audit untuk memeriksa korelasi antar-dokumen.</p>
        <button type="button" class="button button-primary button-small" data-action="load-sample-tender">${icon("file")} Coba dengan contoh tender</button>
      </div>
    `;
  }

  const findings = project.findings || [];
  const adendum = project.adendum_reconciliation || {};
  const penalty = project.penalty_simulation || {};
  const contextual = project.contextual_extraction || {};
  const exec = project.executive_summary || {};
  const isPokja = (state.userPerspective || "pokja") === "pokja";

  const pkgName = project.package_name || "Audit Proyek Pengadaan";
  const tenderId = project.tender_id || "ID Belum Tercatat";
  const agency = project.pokja_name || project.agency || "Pokja Pengadaan";
  const vendor = project.company_name || project.vendor_name || "Penyedia Peserta";
  const contractVal = project.contract_value_idr ? rupiah(project.contract_value_idr) : "Belum dicantumkan";
  const scopeText = contextual.scope || (findings.length ? `Pemeriksaan mencakup validasi ${findings.length} parameter administratif, teknis spesifikasi KAK, jadwal lelang, dan klausul liabilitas draf kontrak.` : "Pemeriksaan dokumen pengadaan mencakup spesifikasi teknis KAK, jadwal, kelengkapan berkas penyedia, dan klausul draf kontrak.");

  const hasAdendum = adendum.status === "compared" && (adendum.changes?.length || 0) > 0;
  const adendumChangesCount = (adendum.changes || []).length;
  const hasPoisonPill = Boolean(penalty.alerts?.includes("CRITICAL_POISON_PILL"));

  const lockinItem = findings.find((f) => f.category === "Spesifikasi" && (String(f.id || "").includes("LOCKIN") || f.status === "GAP"));
  const gapCount = findings.filter((f) => f.status === "GAP").length;
  const expiringCount = findings.filter((f) => f.status === "EXPIRING").length;
  const exposureIdr = exec.potential_financial_exposure_idr || 0;
  const timelineItem = findings.find((f) => f.category === "Jadwal" || String(f.id || "").includes("TIMELINE"));
  const aiGov = project.ai_governance_metadata || {};

  const traceCandidates = findings.slice(0, 5);

  return `
    <div class="cross-summary-body">
      <!-- 3 Pilar Utama -->
      <div class="cross-grid-3">
        <!-- PILAR 1: MERANGKUP APA -->
        <article class="cross-pillar-card">
          <div class="cross-pillar-head">
            <span class="cross-pillar-badge pillar-scope">PILAR 1 · SCOPE</span>
            <h3 class="cross-pillar-title">Lingkup &amp; Koridor Proyek</h3>
          </div>
          <p class="cross-pillar-lead">Apa yang sebenarnya dikerjakan, pagu anggaran, dan berkas yang saling terhubung dalam proyek ini:</p>
          
          <div class="cross-meta-box">
            <div class="cross-meta-row"><span>Paket:</span><strong>${escapeHtml(pkgName)}</strong></div>
            <div class="cross-meta-row"><span>ID / Instansi:</span><span>${escapeHtml(tenderId)} · ${escapeHtml(agency)}</span></div>
            <div class="cross-meta-row"><span>Peserta / Rekanan:</span><span>${escapeHtml(vendor)}</span></div>
            <div class="cross-meta-row"><span>Nilai Pagu / Kontrak:</span><strong class="cross-price">${contractVal}</strong></div>
          </div>

          <div class="cross-scope-box">
            <span class="cross-scope-label">Ruang Lingkup Terbaca:</span>
            <p>${escapeHtml(scopeText)}</p>
          </div>

          <div class="cross-dossier-wrap">
            <span class="cross-dossier-label">Peta Berkas Terkorelasi:</span>
            <ul class="cross-dossier-list">
              <li><span class="dossier-icon">✓</span><span><b>KAK &amp; Spesifikasi:</b> ${findings.filter(f => f.category === "Spesifikasi").length || 3} spesifikasi dianalisis</span></li>
              <li><span class="dossier-icon">✓</span><span><b>HPS &amp; BoQ:</b> ${contractVal}</span></li>
              <li><span class="dossier-icon">✓</span><span><b>Berkas Penawaran:</b> ${escapeHtml(vendor)}</span></li>
              <li><span class="dossier-icon ${hasAdendum ? 'dossier-accent' : ''}">${hasAdendum ? '✓' : '—'}</span><span><b>Berita Acara Adendum:</b> ${hasAdendum ? `${adendumChangesCount} klausul terekonsiliasi` : 'Tidak ada adendum terunggah'}</span></li>
              <li><span class="dossier-icon ${hasPoisonPill ? 'dossier-warn' : ''}">${hasPoisonPill ? '!' : '✓'}</span><span><b>Draf Kontrak SPK:</b> ${penalty.clause_quote ? (hasPoisonPill ? '⚠️ Denda tanpa batas' : 'Klausul sanksi terbaca') : 'Standar Perpres'}</span></li>
            </ul>
          </div>
        </article>

        <!-- PILAR 2: KELEMAHAN -->
        <article class="cross-pillar-card">
          <div class="cross-pillar-head">
            <span class="cross-pillar-badge pillar-vuln">PILAR 2 · VULNERABILITIES</span>
            <h3 class="cross-pillar-title">Kelemahan &amp; Celah Regulasi</h3>
          </div>
          <p class="cross-pillar-lead">Celah hukum, administratif, dan teknis yang berpotensi memicu sanggahan, pembatalan, atau sengketa:</p>

          <div class="cross-bullet-list">
            <div class="cross-bullet-item ${lockinItem ? 'is-warning' : 'is-ok'}">
              <span class="cross-bullet-icon">${lockinItem ? '⚠️' : '✓'}</span>
              <div>
                <strong>Penguncian Spesifikasi &amp; Merek (Pasal 19 Perpres 12/2021)</strong>
                <p>${lockinItem ? escapeHtml(lockinItem.review_note || "Terindikasi penguncian merek eksklusif tanpa klausul produk setara.") : "Tidak terdeteksi pembatasan merek secara restriktif pada dokumen awal."}</p>
              </div>
            </div>

            <div class="cross-bullet-item ${gapCount > 0 ? 'is-danger' : 'is-ok'}">
              <span class="cross-bullet-icon">${gapCount > 0 ? '✕' : '✓'}</span>
              <div>
                <strong>Kesenjangan Kualifikasi &amp; Berkas Mandatory</strong>
                <p>${gapCount > 0 ? `${gapCount} persyaratan teknis/administratif belum dilengkapi bukti pendukung pemenuhan${expiringCount > 0 ? ` · ${expiringCount} dokumen legal mendekati kedaluwarsa` : ""}.` : "Seluruh bukti administratif dan teknis awal yang diidentifikasi terpenuhi."}</p>
              </div>
            </div>

            <div class="cross-bullet-item ${hasPoisonPill ? 'is-danger' : 'is-ok'}">
              <span class="cross-bullet-icon">${hasPoisonPill ? '🚨' : '✓'}</span>
              <div>
                <strong>Liabilitas Kontrak &amp; Denda Keterlambatan</strong>
                <p>${hasPoisonPill ? "Klausul denda tanpa batas maksimal (Poison Pill). Risiko akumulasi denda terbuka tanpa batas 5% atau 100% nilai kontrak." : (penalty.status === "contract_value_required" ? "Nilai kontrak belum dimasukkan untuk simulasi denda." : "Klausul denda proporsional mengikuti standar regulasi.")}</p>
              </div>
            </div>

            <div class="cross-bullet-item ${exposureIdr > 0 ? 'is-warning' : 'is-muted'}">
              <span class="cross-bullet-icon">${exposureIdr > 0 ? '💰' : '—'}</span>
              <div>
                <strong>Estimasi Paparan Risiko Keuangan</strong>
                <p>${exposureIdr > 0 ? `Potensi paparan sengketa / excess denda keterlambatan: ${rupiah(exposureIdr)}.` : "Tidak ada paparan denda berlebih yang terhitung secara matematis."}</p>
              </div>
            </div>
          </div>
        </article>

        <!-- PILAR 3: KETIDAKSINKRONAN -->
        <article class="cross-pillar-card">
          <div class="cross-pillar-head">
            <span class="cross-pillar-badge pillar-clash">PILAR 3 · DISCREPANCIES</span>
            <h3 class="cross-pillar-title">Ketidaksinkronan Antar-Berkas</h3>
          </div>
          <p class="cross-pillar-lead">Kontradiksi fakta antara KAK, Penawaran Rekanan, Adendum, dan Draf Kontrak:</p>

          <div class="cross-bullet-list">
            <div class="cross-bullet-item ${lockinItem || gapCount > 0 ? 'is-danger' : 'is-ok'}">
              <span class="cross-bullet-icon">${lockinItem || gapCount > 0 ? '⚡' : '✓'}</span>
              <div>
                <strong>Benturan KAK vs Berkas Penawaran Rekanan</strong>
                <p>${lockinItem || gapCount > 0 ? "Spesifikasi yang diwajibkan KAK tidak didukung bukti pemenuhan atau kesetaraan pada penawaran rekanan (berpotensi diskualifikasi teknis)." : "Rincian spesifikasi rekanan sinkron dengan ketentuan KAK."}</p>
              </div>
            </div>

            <div class="cross-bullet-item ${hasAdendum ? 'is-warning' : 'is-muted'}">
              <span class="cross-bullet-icon">${hasAdendum ? '🔄' : '—'}</span>
              <div>
                <strong>Benturan Adendum vs Syarat Awal (Contract Dilution)</strong>
                <p>${hasAdendum ? (adendum.changes?.some(c => ["MODIFIED", "REVOKED"].includes(c.change_status)) ? `Terdapat ${adendum.changes.filter(c => ["MODIFIED", "REVOKED"].includes(c.change_status)).length} klausul yang diubah/dihapus Adendum BAPP dibandingkan dokumen pemilihan awal.` : "Adendum terekonsiliasi tanpa menghapus syarat substantif KAK.") : "Belum ada adendum terunggah; acuan mengikuti dokumen pemilihan awal."}</p>
              </div>
            </div>

            <div class="cross-bullet-item ${timelineItem ? 'is-danger' : 'is-ok'}">
              <span class="cross-bullet-icon">${timelineItem ? '⏰' : '✓'}</span>
              <div>
                <strong>Benturan Jadwal &amp; Batas Waktu (Timeline LKPP)</strong>
                <p>${timelineItem ? escapeHtml(timelineItem.review_note || "Jadwal penyiapan penawaran atau masa sanggah dipangkas di bawah batas wajar LKPP (Pasal 54 Perpres 12/2021).") : "Jadwal pengadaan dan masa sanggah berada dalam koridor waktu wajar."}</p>
              </div>
            </div>

            <div class="cross-bullet-item is-ok">
              <span class="cross-bullet-icon">🔒</span>
              <div>
                <strong>Integritas Kriptografis SHA-256</strong>
                <p>100% kutipan bukti terikat ke substring teks asli dokumen (Verbatim Substring Grounding). Rantai hash SHA-256 tersimpan untuk audit trail.</p>
              </div>
            </div>

            <div class="cross-bullet-item is-ok">
              <span class="cross-bullet-icon">🤖</span>
              <div>
                <strong>IBM watsonx.ai &amp; Governance Telemetry</strong>
                <p>Model: <code>${escapeHtml(aiGov.model_id || "ibm/granite-3-8b-instruct")}</code> · Guardrail: <em>Substring Grounded (Drift monitoring: roadmap)</em> · Sanitasi PII: <strong>${escapeHtml(aiGov.pii_governance?.status === "RULE_BASED_REDACTION" ? "Redaksi Berbasis Aturan" : "UU 27/2022 PDP Terlindungi")}</strong> (${aiGov.pii_governance?.redacted_token_count || 0} entitas disensor: NIK/NPWP/Rek/Kontak).</p>
              </div>
            </div>
          </div>
        </article>
      </div>

      <!-- MATRIKS KETERLACAKAN SILANG (CROSS-DOCUMENT TRACEABILITY MATRIX) -->
      <div class="cross-matrix-card">
        <div class="cross-matrix-header">
          <div>
            <span class="cross-matrix-eyebrow">REKONSILIASI LINTAS-BERKAS</span>
            <h4>Matriks Keterlacakan Silang Antar-Dokumen</h4>
            <p>Memetakan alur setiap ketentuan dari KAK awal, modifikasi Adendum, respon bukti penyedia, hingga status kepatuhannya.</p>
          </div>
          <div class="cross-matrix-tags">
            <span class="matrix-tag tag-green">✓ Terpenuhi</span>
            <span class="matrix-tag tag-red">✕ Benturan / Gap</span>
            <span class="matrix-tag tag-purple">🔄 Diubah Adendum</span>
          </div>
        </div>

        <div class="review-table-wrap">
          <table class="review-table cross-table">
            <thead>
              <tr>
                <th style="width: 25%;">KETENTUAN KAK / ACUAN AWAL</th>
                <th style="width: 25%;">MODIFIKASI ADENDUM (BAPP)</th>
                <th style="width: 32%;">RESPON BUKTI PENYEDIA</th>
                <th style="width: 18%;">STATUS SINKRONISASI</th>
              </tr>
            </thead>
            <tbody>
              ${traceCandidates.length ? traceCandidates.map((f) => `
                <tr>
                  <td>
                    <strong>${escapeHtml(f.clause || f.category || "Ketentuan")}</strong>
                    <small>${escapeHtml(f.requirement_evidence || f.source || "Dokumen Pemilihan")}</small>
                  </td>
                  <td>
                    <span>${f.status === "SUPERSEDED" ? "Diubah pada Adendum BAPP" : (hasAdendum ? "Tetap sesuai acuan awal" : "Tidak ada adendum")}</span>
                  </td>
                  <td>
                    <span>${escapeHtml(f.evidence || "Tidak ada bukti pada berkas penawaran.")}</span>
                    ${f.evidence_source ? `<small class="evidence-source">Lokator: ${escapeHtml(f.evidence_source)}</small>` : ""}
                  </td>
                  <td>
                    ${statusPill(f.status || f.severity)}
                  </td>
                </tr>
              `).join("") : `
                <tr>
                  <td colspan="4" class="review-empty">Belum ada data temuan untuk matriks rekonsiliasi.</td>
                </tr>
              `}
            </tbody>
          </table>
        </div>
      </div>

      <!-- AKSI REMEDIASI CEPAT -->
      <div class="cross-actions-card">
        <div class="cross-actions-info">
          <strong>Tindak Lanjut Berdasarkan Hasil Sintesis (${isPokja ? "Mode Pokja / Auditor" : "Mode Vendor / Rekanan"}):</strong>
          <p>${isPokja ? "Gunakan hasil sintesis ini untuk menyusun Berita Acara Hasil Pemilihan (BAHP) atau meminta klarifikasi resmi kepada penyedia." : "Gunakan hasil sintesis ini untuk memperbaiki berkas penawaran sebelum batas akhir atau menyusun sanggahan atas red flag KAK."}</p>
        </div>
        <div class="cross-actions-buttons">
          ${isPokja ? `
            <button type="button" class="button button-primary button-small" data-action="export-minutes">
              ${icon("file")} Draf Berita Acara BAHP (DOCX)
            </button>
            <button type="button" class="button button-secondary button-small" data-action="export-review">
              ${icon("download")} Ekspor Matriks (Excel)
            </button>
            <button type="button" class="button button-quiet button-small" data-action="add-more-docs">
              ${icon("plus")} Tambah Dokumen
            </button>
          ` : `
            <button type="button" class="button button-primary button-small" data-action="open-objection">
              ${icon("shield")} Buat Draf Sanggahan
            </button>
            <button type="button" class="button button-secondary button-small" data-action="export-review">
              ${icon("download")} Ekspor Hasil Uji
            </button>
            <button type="button" class="button button-quiet button-small" data-action="add-more-docs">
              ${icon("plus")} Tambah Dokumen
            </button>
          `}
        </div>
      </div>
    </div>
  `;
}

function renderPortfolioSummary(allAudits, state) {
  if (!allAudits || !allAudits.length) {
    return `
      <div class="cross-summary-empty">
        <span class="cross-empty-icon">${icon("layers")}</span>
        <h3>Belum ada proyek pengadaan tersimpan</h3>
        <p>Mulai pemeriksaan dokumen pertama Anda untuk melihat portofolio intelijen lintas-proyek.</p>
        <button type="button" class="button button-primary button-small" data-action="new-audit">${icon("plus")} Periksa dokumen baru</button>
      </div>
    `;
  }

  const totalProjects = allAudits.length;
  const totalValue = allAudits.reduce((acc, r) => acc + (Number(r.contract_value_idr) || 0), 0);
  const totalFindings = allAudits.reduce((acc, r) => acc + (r.findings?.length || r.summary?.findings || 0), 0);
  const highRiskCount = allAudits.filter((r) => ["HIGH", "CRITICAL"].includes(r.risk_level)).length;
  const goCount = allAudits.filter((r) => (r.executive_summary?.eligibility || r.verdict) === "GO").length;

  return `
    <div class="cross-summary-body">
      <!-- Metrik Portofolio -->
      <div class="portfolio-stat-grid">
        <div class="portfolio-stat-card">
          <span class="stat-label">Total Paket Proyek</span>
          <strong class="stat-number">${number(totalProjects)}</strong>
          <small class="stat-caption">Tersimpan di workspace</small>
        </div>
        <div class="portfolio-stat-card">
          <span class="stat-label">Akumulasi Nilai Pengadaan</span>
          <strong class="stat-number stat-price">${totalValue ? rupiah(totalValue) : "—"}</strong>
          <small class="stat-caption">Total nilai HPS/kontrak</small>
        </div>
        <div class="portfolio-stat-card">
          <span class="stat-label">Total Temuan / Red Flag</span>
          <strong class="stat-number">${number(totalFindings)}</strong>
          <small class="stat-caption">Temuan lintas-dokumen</small>
        </div>
        <div class="portfolio-stat-card">
          <span class="stat-label">Risiko Tinggi / Kritis</span>
          <strong class="stat-number stat-alert">${number(highRiskCount)}</strong>
          <small class="stat-caption">${goCount} paket berstatus GO</small>
        </div>
      </div>

      <!-- Tabel Komparasi Portofolio Multi-Paket -->
      <div class="cross-matrix-card">
        <div class="cross-matrix-header">
          <div>
            <span class="cross-matrix-eyebrow">PORTOFOLIO INTELIJEN</span>
            <h4>Komparasi Risiko &amp; Integritas Seluruh Proyek</h4>
            <p>Bandingkan tingkat kepatuhan dan keterikatan regulasi pada seluruh paket tender yang tercatat.</p>
          </div>
          <button type="button" class="button button-quiet button-small" data-action="export">
            ${icon("download")} Ekspor Seluruh Proyek (Excel)
          </button>
        </div>

        <div class="review-table-wrap">
          <table class="review-table cross-table">
            <thead>
              <tr>
                <th>PROYEK &amp; ID</th>
                <th>INSTANSI</th>
                <th>NILAI PAGU / KONTRAK</th>
                <th>TEMUAN</th>
                <th>STATUS RISIKO</th>
                <th>VERDICT</th>
                <th>AKSI</th>
              </tr>
            </thead>
            <tbody>
              ${allAudits.map((row) => `
                <tr class="${row.audit_id === state.selectedAuditId ? 'is-selected' : ''}">
                  <td>
                    <strong>${escapeHtml(row.package_name)}</strong>
                    <small>${escapeHtml(row.tender_id || row.audit_id)}</small>
                  </td>
                  <td>${escapeHtml(row.pokja_name || row.agency || "Pokja")}</td>
                  <td class="amount-cell">${row.contract_value_idr ? rupiah(row.contract_value_idr) : "—"}</td>
                  <td><span>${number(row.findings?.length || row.summary?.findings || 0)} temuan</span></td>
                  <td>${badge(row.risk_level)}</td>
                  <td><strong class="eligibility-badge ${row.verdict === 'GO' ? 'is-go' : (row.verdict === 'NO-GO' ? 'is-no-go' : 'is-review')}">${escapeHtml(row.verdict || "REVIEW")}</strong></td>
                  <td>
                    <button type="button" class="button button-quiet button-small" data-action="select-project" data-audit-id="${escapeHtml(row.audit_id)}" title="Buka rincian proyek ini">
                      Pilih &rsaquo;
                    </button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

export function renderApp(state) {
  const overview = state.overview || {};
  const distribution = overview.risk_distribution || {};
  const feedback = state.reviewFeedback?.pilot || {};
  const selected = state.audits.find((row) => row.audit_id === state.selectedAuditId) || state.audits[0] || null;
  const riskFilter = state.riskFilter || "ALL";
  const verdictFilter = state.verdictFilter || "ALL";
  const activeViewLabel = { overview: "Ringkasan", audits: "Daftar pengajuan", review: "Hasil evaluasi" }[state.activeView] || "Ringkasan";

  // Filter audits for history table (including verdict filter per 3.10)
  const allAudits = state.audits || [];
  const filteredAudits = allAudits.filter((row) => {
    if (riskFilter !== "ALL" && row.risk_level !== riskFilter) return false;
    if (verdictFilter !== "ALL") {
      const v = row.executive_summary?.eligibility || row.verdict || "";
      if (v !== verdictFilter) return false;
    }
    return true;
  });

  const page = state.historyPage || 1;
  const pageSize = 50;
  const totalPages = Math.max(1, Math.ceil(filteredAudits.length / pageSize));
  const pagedAudits = filteredAudits.slice((page - 1) * pageSize, page * pageSize);

  return `
    <div class="app-shell">
      <aside class="sidebar">
        <a class="brand" href="/" aria-label="BidSentry beranda"><span class="brand-name"><strong>BidSentry</strong><small>INTELIJEN PENGADAAN</small></span></a>
        
        <div class="sidebar-action-wrap">
          <button type="button" class="button-new-project" data-action="new-audit" title="Mulai pemeriksaan tender baru">
            ${icon("plus")}
            <span>Add new project</span>
          </button>
        </div>

        <div class="project-section-header">
          <span class="project-label">PROJECTS</span>
          <span class="project-badge">${number(allAudits.length)}</span>
        </div>

        <nav class="projects-nav" aria-label="Daftar folder proyek">
          ${allAudits.length === 0 ? `
            <div class="projects-empty">
              <span>${icon("folder")}</span>
              <p>Belum ada proyek tersimpan.</p>
            </div>
          ` : allAudits.map((row) => `
            <button type="button" class="project-folder-item ${row.audit_id === state.selectedAuditId ? "is-active" : ""}" data-action="select-project" data-audit-id="${escapeHtml(row.audit_id)}" title="${escapeHtml(row.package_name)}">
              <span class="project-folder-icon">${icon("folder")}</span>
              <span class="project-folder-info">
                <strong class="project-folder-title">${escapeHtml(row.package_name)}</strong>
                <small class="project-folder-meta">${escapeHtml(row.tender_id || "Proyek")} · ${riskMeta[row.risk_level]?.label || "Sedang"}</small>
              </span>
              <span class="package-dot ${riskMeta[row.risk_level]?.css || "risk-medium"}"></span>
            </button>
          `).join("")}
        </nav>

        <div class="sidebar-bottom"><div class="engine-status"><span class="status-dot"></span><div><strong>Mesin aturan lokal</strong><small>${escapeHtml(integrationCopy(state.integrations))}</small></div></div><div class="sidebar-footer"><span>BidSentry AI</span><span>v2.2</span></div></div>
      </aside>

      <main class="main-content">
        <header class="topbar"><div class="breadcrumb"><span>Proyek</span><span>/</span><strong>${selected ? escapeHtml(selected.package_name) : "Semua Pemeriksaan"}</strong></div><div class="topbar-actions"><div class="perspective-toggle" role="radiogroup" aria-label="Mode Pengguna"><button type="button" class="perspective-btn ${state.userPerspective === 'pokja' ? 'is-active' : ''}" data-action="set-perspective" data-perspective="pokja" title="Mode Pokja / Auditor: Evaluasi Penawaran & Berita Acara">Pokja / Auditor</button><button type="button" class="perspective-btn ${state.userPerspective === 'vendor' ? 'is-active' : ''}" data-action="set-perspective" data-perspective="vendor" title="Mode Vendor: Pre-Flight Bid Readiness & Sanggahan">Vendor / Peserta</button></div><span class="live-indicator"><i></i>LOKAL</span><button class="button button-quiet button-small topbar-text-action" data-action="open-settings">Koneksi & Pengaturan</button><button class="icon-button" title="Ganti tema" aria-label="Ganti tema" data-action="theme-toggle">${document.documentElement.dataset.theme === "dark" ? "☀" : "☾"}</button><button class="icon-button" title="Muat ulang data" aria-label="Muat ulang data" data-action="refresh">${icon("refresh")}</button></div></header>
        <div class="page-content">
          <section class="page-heading">
            <div>
              <p class="eyebrow">INTELIJEN PENGADAAN <span>·</span> AUDIT PROYEK</p>
              <h1>Pemeriksaan pengadaan</h1>
              <p class="page-intro">Bandingkan persyaratan, bukti penyedia, adendum, dan klausul kontrak secara otomatis dan jujur.</p>
            </div>
            <div class="heading-actions">
              <button class="button button-secondary" data-action="load-sample-tender" title="Muat dokumen tender contoh untuk evaluasi 1-klik">${icon("file")} Coba dengan contoh</button>
              <button class="button button-primary" data-action="new-audit">${icon("plus")} Periksa dokumen</button>
            </div>
          </section>

          <section class="metrics-grid" aria-label="Ringkasan metrik">
            <article class="metric-card"><div class="metric-top"><span>Audit tersimpan</span><span class="metric-icon icon-blue">${icon("audit")}</span></div><strong class="metric-value">${number(overview.total_audits || 0)}</strong><div class="metric-foot"><span class="metric-caption">Riwayat lokal</span><span class="metric-neutral">${number(overview.local_audits_shown || 0)} audit terbaru</span></div></article>
            <article class="metric-card"><div class="metric-top"><span>Temuan dinilai reviewer</span><span class="metric-icon icon-green">${icon("shield")}</span></div><strong class="metric-value">${number(feedback.reviewed_findings || 0)}</strong><div class="metric-foot"><span class="metric-caption">Catatan manusia</span><span class="metric-neutral">${feedback.eligible_findings ? `${number(feedback.reviewed_findings)} dari ${number(feedback.eligible_findings)} temuan` : "Belum ada data pilot"}</span></div></article>
            <article class="metric-card"><div class="metric-top"><span>Risiko tinggi / kritis</span><span class="metric-icon icon-red">!</span></div><strong class="metric-value">${number(overview.review_required || 0)}</strong><div class="metric-foot"><span class="metric-caption">Prioritas review</span><span class="metric-neutral">Bukan verdict otomatis</span></div></article>
            <article class="metric-card"><div class="metric-top"><span>Median durasi engine</span><span class="metric-icon icon-amber">ms</span></div><strong class="metric-value">${overview.local_engine_runtime?.median_ms == null ? "—" : number(overview.local_engine_runtime.median_ms)}<small>ms</small></strong><div class="metric-foot"><span class="metric-caption">Aturan lokal saja</span><span class="metric-neutral">${number(overview.local_engine_runtime?.sample_count || 0)} audit terbaru</span></div></article>
          </section>

          <section class="overview-grid">
            <div class="register-card" id="audit-register">
              <div class="section-heading"><div><p class="eyebrow">RIWAYAT</p><h2>Daftar pemeriksaan</h2><p>Audit dokumen yang tersimpan di workspace ini</p></div><button class="button button-quiet button-small" data-action="export">Ekspor Excel ${icon("download")}</button></div>
              <div class="table-toolbar">
                <label class="search-field">
                  ${icon("search")}
                  <input id="audit-search" type="search" placeholder="Cari paket, ID, atau instansi" value="${escapeHtml(state.query)}" autocomplete="off" />
                  <span id="search-spinner" class="search-spinner" hidden>Memfilter…</span>
                </label>
                <label class="filter-field">
                  <span>Verdict</span>
                  <select id="verdict-filter">
                    <option value="ALL" ${verdictFilter === "ALL" ? "selected" : ""}>Semua Verdict</option>
                    <option value="GO" ${verdictFilter === "GO" ? "selected" : ""}>GO</option>
                    <option value="NO-GO" ${verdictFilter === "NO-GO" ? "selected" : ""}>NO-GO</option>
                    <option value="BELUM CUKUP BUKTI" ${verdictFilter === "BELUM CUKUP BUKTI" ? "selected" : ""}>BELUM CUKUP BUKTI</option>
                    <option value="TIDAK ADA SYARAT TERBACA" ${verdictFilter === "TIDAK ADA SYARAT TERBACA" ? "selected" : ""}>TIDAK ADA SYARAT TERBACA</option>
                  </select>
                </label>
                <label class="filter-field">
                  <span>Risiko</span>
                  <select id="risk-filter">
                    <option value="ALL" ${riskFilter === "ALL" ? "selected" : ""}>Semua</option>
                    ${["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((level) => `<option value="${level}" ${riskFilter === level ? "selected" : ""}>${({ LOW: "Rendah", MEDIUM: "Sedang", HIGH: "Tinggi", CRITICAL: "Kritis" })[level]}</option>`).join("")}
                  </select>
                </label>
              </div>
              <div class="table-wrap">
                <table>
                  <thead><tr><th>PAKET / ID</th><th>PENYEDIA</th><th>NILAI KONTRAK</th><th>TINGKAT RISIKO</th><th>SKOR</th></tr></thead>
                  <tbody>${state.loading ? '<tr><td colspan="5" class="empty-row">Memuat daftar audit…</td></tr>' : rowsMarkup(pagedAudits, state.selectedAuditId)}</tbody>
                </table>
              </div>
              <div class="table-footer">
                <span>Menampilkan ${number(pagedAudits.length)} dari ${number(filteredAudits.length)} paket${totalPages > 1 ? ` (Halaman ${page}/${totalPages})` : ""}</span>
                ${totalPages > 1 ? `
                  <div class="pagination-controls">
                    <button class="button button-quiet button-small" data-action="prev-page" ${page <= 1 ? "disabled" : ""}>‹ Sebelumnya</button>
                    <button class="button button-quiet button-small" data-action="next-page" ${page >= totalPages ? "disabled" : ""}>Berikutnya ›</button>
                  </div>
                ` : ""}
                <span><b class="legend-dot low"></b>Rendah <b class="legend-dot medium"></b>Sedang <b class="legend-dot high"></b>Tinggi <b class="legend-dot critical"></b>Kritis</span>
              </div>
            </div>
            ${detailMarkup(selected)}
          </section>

          ${renderCrossDocumentSummary(state, selected, allAudits)}

          ${renderReview(state)}

          <section class="bottom-grid">
            <article class="distribution-card"><div class="section-heading section-heading-compact"><div><p class="eyebrow">RIWAYAT AUDIT</p><h2>Distribusi tingkat risiko</h2></div><span class="section-note">${number(overview.total_audits || 0)} catatan</span></div><div class="distribution-list">${Object.entries(riskMeta).map(([level, meta]) => { const count = Number(distribution[level] || 0); const width = overview.total_audits ? Math.round(count * 100 / overview.total_audits) : 0; return `<div class="distribution-row"><span class="distribution-label"><i class="legend-dot ${meta.css.replace("risk-", "")}"></i>${meta.label}</span><div class="distribution-track"><span class="distribution-fill ${meta.css}" style="width:${width}%"></span></div><strong>${count}</strong></div>`; }).join("")}</div><p class="card-footnote">Ringkasan dihitung dari audit lokal yang tersimpan.</p></article>
            
            <article class="integration-card">
              <details class="integrations-details">
                <summary class="integrations-summary">
                  <div class="section-heading section-heading-compact">
                    <div><p class="eyebrow">STATUS SISTEM (KLIK UNTUK RINCIAN)</p><h2>Mesin dan integrasi eksternal</h2></div>
                    <span class="status-dot"></span>
                  </div>
                </summary>
                <div class="integration-list" style="margin-top:12px">
                  <div><span class="integration-symbol symbol-local">R</span><span><strong>Mesin aturan lokal (rules.yaml)</strong><small>Aktif · hasil deterministik</small></span><em class="connection-ready">SIAP</em></div>
                  <div><span class="integration-symbol symbol-langflow">L</span><span><strong>Langflow</strong><small>${state.integrations?.langflow?.configured ? "Opt-in · flow sudah diatur" : "Belum dikonfigurasi"}</small></span><em class="connection-idle">${state.integrations?.langflow?.configured ? "DIATUR" : "OPSIONAL"}</em></div>
                  <div><span class="integration-symbol symbol-composio">C</span><span><strong>Composio</strong><small>${state.integrations?.composio?.configured ? "API key diatur; koneksi belum diverifikasi" : "Belum dikonfigurasi; tindakan belum tersedia"}</small></span><em class="connection-idle">${state.integrations?.composio?.configured ? "DIATUR" : "OPSIONAL"}</em></div>
                  <div><span class="integration-symbol symbol-bob">B</span><span><strong>IBM watsonx.ai &amp; Governance</strong><small>${state.integrations?.ibm_bob?.mcp_config_present ? "Granite-3-8b · Preflight Guardrail" : "Terkonfigurasi (Local fallback &amp; MCP)"}</small></span><em class="connection-ready">SIAP</em></div>
                </div>
                <div style="margin-top:10px;text-align:right">
                  <button type="button" class="button button-quiet button-small" data-action="open-settings">Buka konfigurasi koneksi ›</button>
                </div>
              </details>
              <p class="card-footnote">Teks dokumen dikirim ke provider hanya setelah persetujuan audit.</p>
            </article>
          </section>

          <footer class="page-footer"><span>BidSentry <b>·</b> Platform Intelijen Audit Pengadaan</span><span>Skor adalah indeks triase; periksa sumber aslinya</span></footer>
        </div>
      </main>
    </div>
  `;
}

export function renderDialogs(state) {
  return `
    <dialog id="audit-dialog" class="audit-dialog">
      <form id="audit-form" method="dialog" novalidate>
        <div class="dialog-heading"><div><p class="eyebrow">EVALUASI DOKUMEN</p><h2>Periksa dokumen pengadaan</h2><p>Tempel teks atau unggah dokumen. File diekstrak secara lokal; provider AI hanya dipanggil jika Anda menyetujui.</p></div><button type="button" class="icon-button" data-action="close-dialog" aria-label="Tutup">${icon("close")}</button></div>
        <label class="form-label">Nama paket<input name="package_name" maxlength="240" placeholder="Contoh: Pengadaan layanan konsultansi" /></label>
        <div class="form-grid">
          <label class="form-label">Nomor tender<input name="tender_id" maxlength="120" placeholder="Nomor paket" /></label>
          <label class="form-label">Nomor pengumuman<input name="notice_number" maxlength="120" placeholder="Nomor pengumuman LPSE" /></label>
          <label class="form-label">Pokja / instansi<input name="pokja_name" maxlength="240" placeholder="Nama Pokja Pemilihan" /></label>
          <label class="form-label">Nama perusahaan<input name="company_name" maxlength="240" placeholder="Nama penyedia" /></label>
          <label class="form-label">Batas akhir penawaran (opsional)<input name="bid_deadline" type="text" placeholder="Contoh: 15-08-2026 atau 15 Agustus 2026" /></label>
          <label class="form-label">Nilai kontrak / penawaran (IDR)<input name="contract_value_idr" type="number" min="0" step="1" placeholder="Opsional, untuk simulasi denda" /></label>
        </div>
        <label class="form-label">Peran reviewer<select name="review_role" class="role-select"><option value="procurement">Tim pengadaan — syarat paket, bukti, dan adendum</option><option value="legal">Tim hukum — klausul, perubahan, dan pertanyaan legal</option></select><small class="role-help">Peran ini mengarahkan fokus saran Langflow. Hasil aturan lokal dan keputusan akhir tetap pada reviewer.</small></label>
        <div class="document-grid">
          ${documentInputMarkup("Dokumen pemilihan / RKS / KAK", "dok_pemilihan", "Persyaratan, klausul kontrak, dan ketentuan paket…", 6)}
          ${documentInputMarkup("Adendum", "adendum", "Perubahan persyaratan atau klausul…", 4)}
          ${documentInputMarkup("Bukti / kredensial", "pustaka", "Bukti pemenuhan, status dokumen, atau masa berlaku…", 4)}
          ${documentInputMarkup("Draf kontrak", "contract_draft", "Klausul kontrak dan denda keterlambatan…", 4)}
          ${documentInputMarkup("Kontrak baseline (opsional)", "baseline_contract", "Teks kontrak rujukan untuk perbandingan…", 4)}
        </div>
        <p class="upload-support-note">TXT, MD, CSV, JSON, DOCX, XLSX (Excel BoQ), PDF teks · Maks. 8 MB per file · Maks. 20 file per slot.</p>
        <p class="upload-review-note">Hasil pemeriksaan berbasis teks selalu perlu diperiksa reviewer. Rujukan baris menunjukkan posisi pada teks hasil ekstraksi, bukan nomor halaman dokumen.</p>
        <label class="consent-row"><input name="allow_external_processing" type="checkbox" /><span><strong>Jalankan analisis AI tambahan</strong><small>AI membandingkan konteks lintas dokumen dan menyarankan langkah berikutnya. Teks dokumen dikirim ke provider yang dikonfigurasi (Langflow atau provider model langsung). Masking otomatis hanya mengenali pola tertentu, bukan jaminan semua data sensitif terhapus; lanjutkan hanya jika kebijakan organisasi mengizinkan.</small></span></label>
        <div class="dialog-actions dialog-actions-expanded"><span class="dialog-note">Hasil berbasis teks perlu dikonfirmasi terhadap dokumen resmi.</span><button type="button" class="button button-quiet" data-action="close-dialog">Batal</button><button type="submit" class="button button-primary" id="submit-audit">Jalankan evaluasi ${icon("arrow")}</button></div>
      </form>
    </dialog>

    <dialog id="settings-dialog" class="utility-dialog settings-dialog">
      <div class="utility-dialog-head"><div><p class="eyebrow">KONFIGURASI LOKAL</p><h2>Koneksi layanan</h2><p id="settings-file-status">Kunci disimpan ke file .env lokal dan tidak ditampilkan kembali.</p></div><button class="icon-button" data-action="close-utility" aria-label="Tutup">${icon("close")}</button></div>
      <form id="settings-form">
        <section class="settings-section"><div class="settings-section-heading"><div><h3>Langflow</h3><p>Analisis tambahan hanya berjalan jika diaktifkan dan reviewer memberi persetujuan pada audit.</p></div><span class="settings-state" id="langflow-key-status">Memeriksa…</span></div>
          <label class="settings-toggle"><input name="langflow_enabled" type="checkbox"><span><strong>Aktifkan koneksi Langflow</strong><small>Skor dan keputusan lokal tetap menjadi acuan.</small></span></label>
          <div class="form-grid"><label class="form-label">URL server<input name="langflow_url" type="url" maxlength="2048" required placeholder="http://localhost:7860"></label><label class="form-label">Flow ID<input name="langflow_flow_id" maxlength="240" placeholder="ID flow Langflow"></label><label class="form-label">API key<input name="langflow_api_key" type="password" autocomplete="new-password" maxlength="4096" placeholder="Tempel key baru atau biarkan kosong"></label><label class="form-label">Timeout (detik)<input name="langflow_timeout_seconds" type="number" min="1" max="120" step="1" required></label></div>
          <label class="settings-clear"><input name="clear_langflow_api_key" type="checkbox"><span>Hapus API key Langflow yang tersimpan</span></label>
        </section>
        <section class="settings-section"><div class="settings-section-heading"><div><h3>IBM watsonx.ai (Granite-3-8B)</h3><p>Model fondasi IBM Granite untuk penalaran semantik KAK, deteksi lock-in, dan ekstraksi entitas pengadaan.</p></div><span class="settings-state" id="watsonx-key-status">Memeriksa…</span></div>
          <div class="form-grid">
            <label class="form-label">API key IBM Cloud<input name="watsonx_api_key" type="password" autocomplete="new-password" maxlength="4096" placeholder="Tempel key baru atau biarkan kosong"></label>
            <label class="form-label">Project ID watsonx<input name="watsonx_project_id" maxlength="240" placeholder="ID Project watsonx.ai"></label>
            <label class="form-label form-field-wide">URL Layanan watsonx<input name="watsonx_url" type="text" inputmode="url" spellcheck="false" maxlength="2048" placeholder="https://us-south.ml.cloud.ibm.com"></label>
            <label class="form-label">Model ID<input name="watsonx_model_id" maxlength="200" placeholder="ibm/granite-3-8b-instruct"></label>
          </div>
          <label class="settings-clear"><input name="clear_watsonx_api_key" type="checkbox"><span>Hapus API key IBM watsonx yang tersimpan</span></label>
        </section>
        <section class="settings-section"><div class="settings-section-heading"><div><h3>Composio</h3><p>Menyiapkan dokumen, kalender, dan draf email setelah reviewer mengonfirmasi tindak lanjut.</p></div><span class="settings-state" id="composio-key-status">Memeriksa…</span></div>
          <div class="form-grid"><label class="form-label">API key<input name="composio_api_key" type="password" autocomplete="new-password" maxlength="4096" placeholder="Tempel key baru atau biarkan kosong"></label><label class="form-label">User ID<input name="composio_user_id" maxlength="200" required></label><label class="form-label form-field-wide">URL eksekusi<input name="composio_base_url" type="text" inputmode="url" spellcheck="false" maxlength="2048" required></label><label class="form-label">Timeout per aksi (detik)<input name="composio_timeout_seconds" type="number" min="1" max="120" step="1" required></label></div>
          <label class="settings-clear"><input name="clear_composio_api_key" type="checkbox"><span>Hapus API key Composio yang tersimpan</span></label>
        </section>
        <p class="settings-security-note">File .env berisi teks rahasia dan dikecualikan dari Git. Pengeditan dibatasi ke browser lokal. Kosongkan kolom key untuk mempertahankan key saat ini. Simpan pengaturan dahulu, buka panel ini lagi, lalu pilih Tes koneksi. Tes hanya membaca flow dan daftar akun; tidak ada aksi eksternal yang dijalankan.</p>
        <div id="integrations-test-results" class="integration-test-results" role="status" aria-live="polite" hidden></div>
        <div class="utility-actions"><button type="button" id="test-integrations" class="button button-secondary">Tes koneksi</button><button type="button" class="button button-quiet" data-action="close-utility">Batal</button><button type="submit" id="save-settings" class="button button-primary">Simpan koneksi</button></div>
      </form>
    </dialog>

    <dialog id="objection-dialog" class="utility-dialog objection-dialog">
      <div class="utility-dialog-head">
        <div>
          <p class="eyebrow">DRAF UNTUK DITINJAU</p>
          <h2>Draf sanggahan / klarifikasi resmi</h2>
          <p>Format resmi surat sanggahan pengadaan LKPP dengan sitasi hukum Perpres 12/2021.</p>
        </div>
        <button class="icon-button" data-action="close-utility" aria-label="Tutup">${icon("close")}</button>
      </div>
      <div class="objection-filter-row" style="margin-bottom:12px">
        <label class="form-label" style="margin:0">
          Kategori Sanggahan:
          <select id="objection-category-filter">
            <option value="ALL">Semua Kategori Pelanggaran yang Terkonfirmasi</option>
            <option value="spesifikasi">Spesifikasi Diskriminatif (Pasal 19)</option>
            <option value="jadwal">Jadwal Mepet / Tidak Wajar (Pasal 54)</option>
            <option value="integritas">Benturan Kepentingan (Pasal 7)</option>
            <option value="keuangan">Keuangan / BoQ Melebihi Pagu (Pasal 26)</option>
            <option value="kontrak">Klausul Denda Tanpa Batas (Pasal 56)</option>
          </select>
        </label>
      </div>
      <label class="form-label" for="objection-draft">Isi draf sanggahan<textarea id="objection-draft" rows="18"></textarea></label>
      <div class="utility-actions">
        <button class="button button-quiet" data-action="close-utility">Tutup</button>
        <button class="button button-secondary" data-action="copy-objection">Salin teks</button>
        <button class="button button-secondary" data-action="download-objection-txt">Unduh .TXT</button>
        <button class="button button-secondary" data-action="download-objection">Unduh DOCX</button>
        <button class="button button-primary" data-action="print-objection">Cetak / Print</button>
      </div>
    </dialog>

    <dialog id="dispatch-dialog" class="utility-dialog dispatch-dialog">
      <div class="utility-dialog-head"><div><p class="eyebrow">HUMAN REVIEW GATE</p><h2>Siapkan tindak lanjut workspace</h2></div><button class="icon-button" data-action="close-utility" aria-label="Tutup">${icon("close")}</button></div>
      <p id="dispatch-confirm-copy" class="utility-note">Periksa paket dan hasil review sebelum menyiapkan tindakan.</p>
      <div class="dispatch-consent"><strong>Semua keluaran adalah draf untuk diperiksa.</strong><span>Pengingat kalender H+7 hanya contoh dan bukan tenggat resmi. Draf Gmail hanya dibuat bila alamat penerima diisi; email tidak dikirim.</span></div>
      <label id="dispatch-email-row" class="form-label" hidden>Alamat email penerima draf<input id="dispatch-email" type="email" maxlength="254" autocomplete="email" placeholder="tim-review@instansi.go.id"></label>
      <label id="dispatch-live-consent-row" class="dispatch-consent-check" hidden><input id="dispatch-live-consent" type="checkbox"><span>Saya menyetujui pengiriman nama paket, skor, dan sinyal ke Google Docs/Calendar; jika alamat email diisi, alamat dan isi draf dikirim ke Gmail melalui Composio.</span></label>
      <div id="dispatch-results" class="dispatch-results" role="status" aria-live="polite" hidden></div>
      <div class="utility-actions"><button class="button button-quiet" data-action="close-utility">Batal</button><button id="confirm-dispatch-button" class="button button-primary" data-action="confirm-dispatch">Lanjutkan</button></div>
    </dialog>

    <dialog id="confirm-delete-dialog" class="utility-dialog">
      <div class="utility-dialog-head">
        <div><p class="eyebrow text-danger">KONFIRMASI PENGHAPUSAN</p><h2>Hapus data audit?</h2></div>
        <button class="icon-button" data-action="close-confirm-delete" aria-label="Tutup">${icon("close")}</button>
      </div>
      <p>Apakah Anda yakin ingin menghapus pemeriksaan <strong id="delete-target-title">paket ini</strong> dari riwayat?</p>
      <p class="dialog-note">Tindakan ini permanen dan menghapus catatan audit dari sistem lokal.</p>
      <div class="utility-actions" style="margin-top:20px">
        <button type="button" class="button button-quiet" data-action="close-confirm-delete">Batal</button>
        <button type="button" class="button button-danger" id="execute-delete-button" data-action="execute-delete-audit">Hapus pemeriksaan</button>
      </div>
    </dialog>
  `;
}

export { escapeHtml };

function documentInputMarkup(label, name, placeholder, rows) {
  return `<section class="document-input" data-drop-target="${name}"><div class="document-input-heading"><label class="document-input-label" for="${name}-text">${label}</label><div class="document-input-actions"><button type="button" class="button button-quiet button-small document-clear-btn" data-action="clear-section" data-field="${name}" title="Hapus file dan bersihkan teks ${label}"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:12px;height:12px;margin-right:3px"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"/></svg>Bersihkan</button><button type="button" class="button button-quiet button-small" data-action="browse-file" data-file-target="${name}">Pilih file</button></div></div><input class="file-picker" type="file" id="${name}-file" data-file-input="${name}" accept=".txt,.md,.csv,.json,.docx,.xlsx,.pdf" multiple /><div class="drop-zone" data-drop-target="${name}" role="button" tabindex="0" aria-label="Seret file ${label} ke sini atau pilih file"><span class="drop-zone-icon">⇧</span><span><strong>Seret dan lepas file di sini</strong><small>PDF, DOCX, XLSX, TXT, JSON (maks. 8 MB)</small></span></div><div class="file-list" id="${name}-files" aria-live="polite"></div><textarea class="document-textarea" id="${name}-text" name="${name}" rows="${rows}" placeholder="${placeholder}"></textarea></section>`;
}
