import { renderReview } from "./review.js";

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
  if (!rows.length) return '<tr><td colspan="5" class="empty-row">Belum ada audit tersimpan atau tidak ada yang cocok dengan pencarian.</td></tr>';
  return rows.map((row) => `
    <tr class="audit-row ${row.audit_id === selectedId ? "is-selected" : ""}" data-action="select-audit" data-audit-id="${escapeHtml(row.audit_id)}" tabindex="0" aria-label="Lihat audit ${escapeHtml(row.package_name)}">
      <td><div class="package-cell"><span class="package-dot ${riskMeta[row.risk_level]?.css || "risk-medium"}"></span><span><strong>${escapeHtml(row.package_name)}</strong><small>${escapeHtml(row.tender_id || row.audit_id)} · ${escapeHtml(row.agency || "Workspace lokal")}</small></span></div></td>
      <td>${escapeHtml(row.vendor_name || "—")}</td><td class="amount-cell">${row.contract_value_idr ? rupiah(row.contract_value_idr) : "—"}</td>
      <td>${badge(row.risk_level)}</td><td><span class="score-cell">${number(row.risk_score)}<small>/100</small></span></td>
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
      <div class="detail-head"><div><p class="eyebrow">ANALISIS PAKET</p><h2>${escapeHtml(row.package_name)}</h2><p class="detail-subtitle">${escapeHtml(row.tender_id || row.audit_id)} · ${escapeHtml(row.agency || "Workspace lokal")}</p></div>${icon("arrow")}</div>
      <div class="score-panel"><div class="score-ring ${levelClass}" style="--score:${Math.max(0, Math.min(100, Number(row.risk_score || 0)))}"><div><strong>${number(row.risk_score)}</strong><small>/100</small></div></div><div><span class="eyebrow">INDEKS TRIAGE</span>${badge(row.risk_level)}<p>Indeks aturan untuk membantu prioritas review, bukan probabilitas fraud. Skor 0 berarti tidak ada pemicu berbobot yang terdeteksi; bukan bukti paket bebas risiko.</p></div></div>
      <div class="detail-stats"><div><span>Temuan</span><strong>${number(findings.length || row.summary?.findings || 0)}</strong></div><div><span>Nilai kontrak</span><strong>${row.contract_value_idr ? rupiah(row.contract_value_idr) : "—"}</strong></div><div><span>Sumber</span><strong>${sourceLabel}</strong></div></div>
      <div class="finding-heading"><h3>Temuan untuk ditinjau</h3><span>${number(findingCount)} total</span></div>
      <div class="finding-list">${preview.length ? preview.map((finding) => `<article class="finding-item"><div class="finding-mark ${["CRITICAL", "HIGH"].includes(finding.severity) ? "mark-high" : "mark-low"}"></div><div><div class="finding-title-row"><strong>${escapeHtml(finding.clause || finding.category || "Temuan")}</strong>${statusPill(finding.status || finding.severity)}</div><p>${escapeHtml(finding.evidence || finding.review_note || "Periksa sumber dokumen.")}</p><small>${escapeHtml(finding.source || "Sumber belum ditentukan")}</small></div></article>`).join("") : findingCount ? '<div class="no-findings">Log menyimpan jumlah dan status temuan, bukan kutipan dokumen. Buka sumber asli untuk pemeriksaan bukti.</div>' : '<div class="no-findings">Belum ada temuan yang disimpan pada audit ini.</div>'}</div>
      <div class="detail-actions"><button class="button button-secondary button-small" data-action="dispatch-selected">Siapkan tindak lanjut ${icon("arrow")}</button><button class="button button-quiet button-small" data-action="export-selected-review" aria-label="Ekspor Risk Review paket ini ke Excel">Ekspor Risk Review ${icon("download")}</button></div>
      <p class="detail-caveat">Hasil tersimpan tanpa teks dokumen. Periksa kembali sumber asli sebelum mengambil keputusan.</p>
    </section>`;
}

function integrationCopy(integrations) {
  if (!integrations) return "Memeriksa koneksi";
  if (integrations.langflow?.configured) return "Langflow opt-in tersedia";
  return "Audit lokal aktif · Langflow opsional";
}

export function renderApp(state) {
  const overview = state.overview || {};
  const distribution = overview.risk_distribution || {};
  const feedback = state.reviewFeedback?.pilot || {};
  const selected = state.audits.find((row) => row.audit_id === state.selectedAuditId) || state.audits[0] || null;
  const riskFilter = state.riskFilter || "ALL";
  const activeViewLabel = { overview: "Ringkasan", audits: "Daftar pengajuan", review: "Hasil evaluasi" }[state.activeView] || "Ringkasan";
  return `
    <div class="app-shell">
      <aside class="sidebar">
        <a class="brand" href="/" aria-label="BidSentry beranda"><span class="brand-name"><strong>BidSentry</strong><small>INTELIJEN PENGADAAN</small></span></a>
        <div class="workspace-switch"><span><strong>Ruang kerja</strong><small>Pengadaan publik</small></span><span class="chevron">⌄</span></div>
        <p class="nav-label">RUANG KERJA</p>
        <nav class="primary-nav" aria-label="Navigasi utama">
          <button class="nav-item ${state.activeView === "overview" ? "active" : ""}" data-action="view-overview">${icon("overview")}<span>Ringkasan</span><kbd>01</kbd></button>
          <button class="nav-item ${state.activeView === "audits" ? "active" : ""}" data-action="focus-audits">${icon("audit")}<span>Daftar pengajuan</span><kbd>${number(overview.total_audits || 0)}</kbd></button>
          <button class="nav-item ${state.activeView === "review" ? "active" : ""}" data-action="focus-review">${icon("shield")}<span>Hasil evaluasi</span></button>
        </nav>
        <div class="sidebar-bottom"><div class="engine-status"><span class="status-dot"></span><div><strong>Mesin aturan lokal</strong><small>${escapeHtml(integrationCopy(state.integrations))}</small></div></div><div class="sidebar-footer"><span>BidSentry AI</span><span>v2.1</span></div></div>
      </aside>

      <main class="main-content">
        <header class="topbar"><div class="breadcrumb"><span>Ruang kerja</span><span>/</span><strong>${activeViewLabel}</strong></div><div class="topbar-actions"><span class="live-indicator"><i></i>LOKAL</span><button class="button button-quiet button-small topbar-text-action" data-action="open-settings">Koneksi</button><button class="icon-button" title="Ganti tema" aria-label="Ganti tema" data-action="theme-toggle">${document.documentElement.dataset.theme === "dark" ? "☀" : "☾"}</button><button class="icon-button" title="Muat ulang data" aria-label="Muat ulang data" data-action="refresh">${icon("refresh")}</button></div></header>
        <div class="page-content">
          <section class="page-heading"><div><p class="eyebrow">INTELIJEN PENGADAAN <span>·</span> RUANG KERJA</p><h1>Pemeriksaan pengadaan</h1><p class="page-intro">Bandingkan persyaratan, bukti penyedia, adendum, dan klausul kontrak.</p></div><button class="button button-primary" data-action="new-audit">${icon("plus")} Periksa dokumen</button></section>
          <section class="metrics-grid" aria-label="Ringkasan metrik">
            <article class="metric-card"><div class="metric-top"><span>Audit tersimpan</span><span class="metric-icon icon-blue">${icon("audit")}</span></div><strong class="metric-value">${number(overview.total_audits || 0)}</strong><div class="metric-foot"><span class="metric-caption">Riwayat lokal</span><span class="metric-neutral">${number(overview.local_audits_shown || 0)} audit terbaru</span></div></article>
            <article class="metric-card"><div class="metric-top"><span>Temuan dinilai reviewer</span><span class="metric-icon icon-green">${icon("shield")}</span></div><strong class="metric-value">${number(feedback.reviewed_findings || 0)}</strong><div class="metric-foot"><span class="metric-caption">Catatan manusia</span><span class="metric-neutral">${feedback.eligible_findings ? `${number(feedback.reviewed_findings)} dari ${number(feedback.eligible_findings)} temuan` : "Belum ada data pilot"}</span></div></article>
            <article class="metric-card"><div class="metric-top"><span>Risiko tinggi / kritis</span><span class="metric-icon icon-red">!</span></div><strong class="metric-value">${number(overview.review_required || 0)}</strong><div class="metric-foot"><span class="metric-caption">Prioritas review</span><span class="metric-neutral">Bukan verdict otomatis</span></div></article>
            <article class="metric-card"><div class="metric-top"><span>Median durasi engine</span><span class="metric-icon icon-amber">ms</span></div><strong class="metric-value">${overview.local_engine_runtime?.median_ms == null ? "—" : number(overview.local_engine_runtime.median_ms)}<small>ms</small></strong><div class="metric-foot"><span class="metric-caption">Aturan lokal saja</span><span class="metric-neutral">${number(overview.local_engine_runtime?.sample_count || 0)} audit terbaru</span></div></article>
          </section>
          <section class="overview-grid">
            <div class="register-card" id="audit-register">
              <div class="section-heading"><div><p class="eyebrow">RIWAYAT</p><h2>Daftar pemeriksaan</h2><p>Audit dokumen yang tersimpan di workspace ini</p></div><button class="button button-quiet button-small" data-action="export">Ekspor Excel ${icon("download")}</button></div>
              <div class="table-toolbar"><label class="search-field">${icon("search")}<input id="audit-search" type="search" placeholder="Cari paket, ID, atau instansi" value="${escapeHtml(state.query)}" autocomplete="off" /></label><label class="filter-field"><span>Risiko</span><select id="risk-filter"><option value="ALL" ${riskFilter === "ALL" ? "selected" : ""}>Semua</option>${["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((level) => `<option value="${level}" ${riskFilter === level ? "selected" : ""}>${({ LOW: "Rendah", MEDIUM: "Sedang", HIGH: "Tinggi", CRITICAL: "Kritis" })[level]}</option>`).join("")}</select></label></div>
              <div class="table-wrap"><table><thead><tr><th>PAKET / ID</th><th>PENYEDIA</th><th>NILAI KONTRAK</th><th>TINGKAT RISIKO</th><th>SKOR</th></tr></thead><tbody>${state.loading ? '<tr><td colspan="5" class="empty-row">Memuat daftar audit…</td></tr>' : rowsMarkup(state.audits, state.selectedAuditId)}</tbody></table></div>
              <div class="table-footer"><span>Menampilkan ${number(state.audits.length)} paket</span><span><b class="legend-dot low"></b>Rendah <b class="legend-dot medium"></b>Sedang <b class="legend-dot high"></b>Tinggi <b class="legend-dot critical"></b>Kritis</span></div>
            </div>
            ${detailMarkup(selected)}
          </section>
          ${renderReview(state)}
          <section class="bottom-grid">
            <article class="distribution-card"><div class="section-heading section-heading-compact"><div><p class="eyebrow">RIWAYAT AUDIT</p><h2>Distribusi tingkat risiko</h2></div><span class="section-note">${number(overview.total_audits || 0)} catatan</span></div><div class="distribution-list">${Object.entries(riskMeta).map(([level, meta]) => { const count = Number(distribution[level] || 0); const width = overview.total_audits ? Math.round(count * 100 / overview.total_audits) : 0; return `<div class="distribution-row"><span class="distribution-label"><i class="legend-dot ${meta.css.replace("risk-", "")}"></i>${meta.label}</span><div class="distribution-track"><span class="distribution-fill ${meta.css}" style="width:${width}%"></span></div><strong>${count}</strong></div>`; }).join("")}</div><p class="card-footnote">Ringkasan dihitung dari audit lokal yang tersimpan.</p></article>
            <article class="integration-card"><div class="section-heading section-heading-compact"><div><p class="eyebrow">STATUS SISTEM</p><h2>Mesin dan koneksi</h2></div><span class="status-dot"></span></div><div class="integration-list"><div><span class="integration-symbol symbol-local">R</span><span><strong>Mesin aturan lokal</strong><small>Aktif · hasil deterministik</small></span><em class="connection-ready">SIAP</em></div><div><span class="integration-symbol symbol-langflow">L</span><span><strong>Langflow</strong><small>${state.integrations?.langflow?.configured ? "Opt-in · flow sudah diatur" : "Belum dikonfigurasi"}</small></span><em class="connection-idle">${state.integrations?.langflow?.configured ? "DIATUR" : "OPSIONAL"}</em></div><div><span class="integration-symbol symbol-composio">C</span><span><strong>Composio</strong><small>${state.integrations?.composio?.configured ? "API key diatur; koneksi belum diverifikasi" : "Belum dikonfigurasi; tindakan belum tersedia"}</small></span><em class="connection-idle">${state.integrations?.composio?.configured ? "DIATUR" : "OPSIONAL"}</em></div><div><span class="integration-symbol symbol-bob">B</span><span><strong>IBM Bob / MCP</strong><small>${state.integrations?.ibm_bob?.mcp_config_present ? "Konfigurasi MCP tersedia; koneksi belum diverifikasi" : "Belum terhubung"}</small></span><em class="connection-idle">MCP</em></div></div><p class="card-footnote">Teks dokumen dikirim ke provider hanya setelah persetujuan audit.</p></article>
          </section>
          <footer class="page-footer"><span>BidSentry <b>·</b> Ruang kerja pemeriksaan internal</span><span>Skor adalah indeks triase; periksa sumber aslinya</span></footer>
        </div>
      </main>
    </div>
    <dialog id="audit-dialog" class="audit-dialog">
      <form id="audit-form" method="dialog" novalidate>
        <div class="dialog-heading"><div><p class="eyebrow">EVALUASI DOKUMEN</p><h2>Periksa dokumen pengadaan</h2><p>Tempel teks atau unggah dokumen. File diekstrak secara lokal; provider AI hanya dipanggil jika Anda menyetujui.</p></div><button type="button" class="icon-button" data-action="close-dialog" aria-label="Tutup">${icon("close")}</button></div>
        <label class="form-label">Nama paket<input name="package_name" maxlength="240" placeholder="Contoh: Pengadaan layanan konsultansi" /></label>
        <div class="form-grid"><label class="form-label">Nomor tender<input name="tender_id" maxlength="120" placeholder="Nomor paket" /></label><label class="form-label">Nomor pengumuman<input name="notice_number" maxlength="120" placeholder="Nomor pengumuman LPSE" /></label><label class="form-label">Pokja / instansi<input name="pokja_name" maxlength="240" placeholder="Nama Pokja Pemilihan" /></label><label class="form-label">Nama perusahaan<input name="company_name" maxlength="240" placeholder="Nama penyedia" /></label><label class="form-label form-field-wide">Nilai kontrak / penawaran (IDR)<input name="contract_value_idr" type="number" min="0" step="1" placeholder="Opsional, untuk simulasi denda" /></label></div>
        <label class="form-label">Peran reviewer<select name="review_role" class="role-select"><option value="procurement">Tim pengadaan — syarat paket, bukti, dan adendum</option><option value="legal">Tim hukum — klausul, perubahan, dan pertanyaan legal</option></select><small class="role-help">Peran ini mengarahkan fokus saran Langflow. Hasil aturan lokal dan keputusan akhir tetap pada reviewer.</small></label>
        <div class="document-grid">
          ${documentInputMarkup("Dokumen pemilihan / RKS / KAK", "dok_pemilihan", "Persyaratan, klausul kontrak, dan ketentuan paket…", 6)}
          ${documentInputMarkup("Adendum", "adendum", "Perubahan persyaratan atau klausul…", 4)}
          ${documentInputMarkup("Bukti / kredensial", "pustaka", "Bukti pemenuhan, status dokumen, atau masa berlaku…", 4)}
          ${documentInputMarkup("Draf kontrak", "contract_draft", "Klausul kontrak dan denda keterlambatan…", 4)}
          ${documentInputMarkup("Kontrak baseline (opsional)", "baseline_contract", "Teks kontrak rujukan untuk perbandingan…", 4)}
        </div>
        <p class="upload-support-note">TXT, MD, CSV, JSON, DOCX, PDF teks · Maks. 8 MB dan 500 halaman PDF per file · Maks. 20 file per unggahan. PDF hasil scan memerlukan OCR.</p>
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
        <section class="settings-section"><div class="settings-section-heading"><div><h3>Composio</h3><p>Menyiapkan dokumen, kalender, dan draf email setelah reviewer mengonfirmasi tindak lanjut.</p></div><span class="settings-state" id="composio-key-status">Memeriksa…</span></div>
          <div class="form-grid"><label class="form-label">API key<input name="composio_api_key" type="password" autocomplete="new-password" maxlength="4096" placeholder="Tempel key baru atau biarkan kosong"></label><label class="form-label">User ID<input name="composio_user_id" maxlength="200" required></label><label class="form-label form-field-wide">URL eksekusi<input name="composio_base_url" type="text" inputmode="url" spellcheck="false" maxlength="2048" required></label><label class="form-label">Timeout per aksi (detik)<input name="composio_timeout_seconds" type="number" min="1" max="120" step="1" required></label></div>
          <label class="settings-clear"><input name="clear_composio_api_key" type="checkbox"><span>Hapus API key Composio yang tersimpan</span></label>
        </section>
        <p class="settings-security-note">File .env berisi teks rahasia dan dikecualikan dari Git. Pengeditan dibatasi ke browser lokal. Kosongkan kolom key untuk mempertahankan key saat ini. Simpan pengaturan dahulu, buka panel ini lagi, lalu pilih Tes koneksi. Tes hanya membaca flow dan daftar akun; tidak ada aksi eksternal yang dijalankan.</p>
        <div id="integrations-test-results" class="integration-test-results" role="status" aria-live="polite" hidden></div>
        <div class="utility-actions"><button type="button" id="test-integrations" class="button button-secondary">Tes koneksi</button><button type="button" class="button button-quiet" data-action="close-utility">Batal</button><button type="submit" id="save-settings" class="button button-primary">Simpan koneksi</button></div>
      </form>
    </dialog>
    <dialog id="objection-dialog" class="utility-dialog objection-dialog"><div class="utility-dialog-head"><div><p class="eyebrow">DRAF UNTUK DITINJAU</p><h2>Draf sanggahan / klarifikasi</h2><p>Sesuaikan identitas, nomor paket, fakta, dan sitasi; minta tim legal meninjau sebelum dipakai.</p></div><button class="icon-button" data-action="close-utility" aria-label="Tutup">${icon("close")}</button></div><label class="form-label" for="objection-draft">Isi draf<textarea id="objection-draft" rows="18"></textarea></label><div class="utility-actions"><button class="button button-quiet" data-action="close-utility">Tutup</button><button class="button button-secondary" data-action="copy-objection">Salin draf</button><button class="button button-secondary" data-action="download-objection">Unduh DOCX</button><button class="button button-primary" data-action="print-objection">Cetak</button></div></dialog>
    <dialog id="dispatch-dialog" class="utility-dialog dispatch-dialog"><div class="utility-dialog-head"><div><p class="eyebrow">HUMAN REVIEW GATE</p><h2>Siapkan tindak lanjut workspace</h2></div><button class="icon-button" data-action="close-utility" aria-label="Tutup">${icon("close")}</button></div><p id="dispatch-confirm-copy" class="utility-note">Periksa paket dan hasil review sebelum menyiapkan tindakan.</p><div class="dispatch-consent"><strong>Semua keluaran adalah draf untuk diperiksa.</strong><span>Pengingat kalender H+7 hanya contoh dan bukan tenggat resmi. Draf Gmail hanya dibuat bila alamat penerima diisi; email tidak dikirim.</span></div><label id="dispatch-email-row" class="form-label" hidden>Alamat email penerima draf<input id="dispatch-email" type="email" maxlength="254" autocomplete="email" placeholder="tim-review@instansi.go.id"></label><label id="dispatch-live-consent-row" class="dispatch-consent-check" hidden><input id="dispatch-live-consent" type="checkbox"><span>Saya menyetujui pengiriman nama paket, skor, dan sinyal ke Google Docs/Calendar; jika alamat email diisi, alamat dan isi draf dikirim ke Gmail melalui Composio.</span></label><div id="dispatch-results" class="dispatch-results" role="status" aria-live="polite" hidden></div><div class="utility-actions"><button class="button button-quiet" data-action="close-utility">Batal</button><button id="confirm-dispatch-button" class="button button-primary" data-action="confirm-dispatch">Lanjutkan</button></div></dialog>`;
}

export { escapeHtml };

function documentInputMarkup(label, name, placeholder, rows) {
  return `<section class="document-input" data-drop-target="${name}"><div class="document-input-heading"><label class="form-label" for="${name}-text">${label}</label><button type="button" class="button button-quiet button-small" data-action="browse-file" data-file-target="${name}">Pilih file</button></div><input class="file-picker" type="file" id="${name}-file" data-file-input="${name}" accept=".txt,.md,.csv,.json,.docx,.pdf" multiple /><div class="drop-zone" data-drop-target="${name}" role="button" tabindex="0" aria-label="Seret file ${label} ke sini atau pilih file"><span class="drop-zone-icon">⇧</span><span><strong>Seret dan lepas file di sini</strong><small>atau pilih file dari perangkat</small></span></div><p class="file-list" id="${name}-files" aria-live="polite"></p><textarea id="${name}-text" name="${name}" rows="${rows}" placeholder="${placeholder}"></textarea></section>`;
}
