# Judge readiness

## Score sheet as supplied

| Element | Weight | Demonstration and evidence |
|---|---:|---|
| Problem clarity and relevance | 20% | Explain the procurement review workflow and show a clause with its extracted-text source. Bring interviews, workflow observations, or a validated user problem; the included package examples are synthetic. |
| Innovation, creativity, feasibility, monetization | 25% | Show local-first rule signals, document drop, evidence review, human confirmation, and optional integrations. Present per-workspace subscription and integration tiers only as a business hypothesis until willingness to pay and operating costs are validated. |
| User impact and benefits | 15% | Show the reviewer path from source document to a documented follow-up. In a pilot, measure time to first review, findings with traceable citations, and how often reviewers confirm or dismiss signals. No real-world impact data is currently claimed. |
| Technical execution and prototype functionality | 20% | Run the app, drop a supported file, inspect an evidence reference, filter the register, and export. Report live integrations only after a successful end-to-end check; otherwise show the local fallback honestly. |
| Responsible AI implementation | 10% | Describe scores as uncalibrated triage indices, never fraud probabilities or verdicts. Show human review, per-audit Langflow consent, local fallback, and metadata-only audit logging. |
| Hackathon class participation | 5% | Keep independent proof of attendance, checkpoints, each team member's contribution, and the final demo. The product cannot establish program participation by itself. |

The listed weights total **95%**. The remaining 5% is not specified in the supplied sheet. Ask the organizers how to handle it; do not normalize or estimate the final weighted score without their direction.

The reference fixture has been labeled as synthetic and not benchmarked. Earlier accuracy, confidence, latency, and “ground truth” claims had no supporting evaluation record, so those values were removed. The dashboard no longer converts a low synthetic risk band into a “compliance rate.” Do not cite the three fixture cases as measured model performance.

Custom findings can now receive a manual disposition: supported by evidence, needs more information, or not supported. BidSentry stores the audit ID, finding ID, selected label, and timestamp only. The UI and export show counts and coverage as **reviewer input**, not accuracy, independent adjudication, or user impact. Counts become evidence only after reviewers actually use the feature; this workspace currently has no prefilled feedback.

## Checklist Kesiapan Juri: Resolusi 8 Red Flag Teknis & Strategis

Berikut adalah verifikasi kepatuhan seluruh perbaikan arsitektural dan evaluasi terhadap 8 red flag utama:

| No | Red Flag Audit Awal | Status Resolusi | Bukti Implementasi & Verifikasi |
|---|---|:---:|---|
| 1 | **Hardcoded Demo Values** (Nilai angka Rp 10.16 M / 8.5 M tertanam di kode) | **RESOLVED** | Nilai statis dihapus total. Ekstraksi dinamis angka Pagu dan BoQ berbasis parser teks & tabel Excel/PDF (`bidsentry.evaluators.engine`). Lolos 13 skenario probe dinamis. |
| 2 | **Data Leakage & Benchmark Overfitting** (Label diubah pasca-eksekusi) | **RESOLVED** | Pemisahan tegas 3 dataset: Development Set (24 docs, dipandu aturan), Validation Set v1 (10 blind docs, **label beku** tanpa penyesuaian, akurasi 90.0%, 3/3 traps lolos), dan Narrative Set (5 docs baru, akurasi 80.0%, 1/1 trap). |
| 3 | **Klaim & Metrik Tanpa Sumber** (Statistik tanpa verifikasi empiris) | **RESOLVED** | Seluruh klaim eksternal disinkronkan dengan data resmi LKPP 2024 atau diberi label *"BELUM DIVERIFIKASI" / "BELUM DIKUMPULKAN"*. Tidak ada pemalsuan testimoni atau wawancara. |
| 4 | **Ketiadaan Perspektif Pengguna Ganda (Role-Based UX)** | **RESOLVED** | Implementasi Dual Mode di UI: **Mode Panitia / Pokja** (evaluasi multi-vendor, Berita Acara BAHP DOCX) vs **Mode Peserta / Vendor** (pre-flight check, draf Sanggahan DOCX) dengan tombol switch instan. |
| 5 | **Pengujian Hanya Dokumen Teks Bersih (.txt)** | **RESOLVED** | Pembuatan dan pengujian berkas PDF multi-halaman realistis: `paket_konstruksi_rab_kompleks.pdf` (tabel BoQ multi-halaman) dan `paket_pengadaan_it_server_kak.pdf` (KAK lengkap). Diverifikasi via `tests/test_pdf_real_extraction.py`. |
| 6 | **Integrasi IBM watsonx.ai Belum Eksplisit** | **RESOLVED** | Modul `WatsonxService` aktif dengan model `ibm/granite-3-8b-instruct`, decoding greedy, pembersihan PII otomatis pra-inferensi, dan simulasi guardrail watsonx.governance. Diverifikasi via `scripts/verify_watsonx.py`. |
| 7 | **Duplikasi Modul & Inkonsistensi Arsitektur** | **RESOLVED** | Depresiasi `http_server.py` mendukung server tunggal `server.py` / `bidsentry.asgi`; konsolidasi skema di `bidsentry.schemas`; konsolidasi audit finansial di `bidsentry.audits.financial`. Terdokumentasi di `docs/ARCHITECTURE_CONSOLIDATED.md`. |
| 8 | **Responsible AI & Risiko Bias Algoritmik** | **RESOLVED** | Proteksi afirmasi UMKM sesuai **Pasal 65 Perpres 12/2021 & PP 7/2021** (merelaksasi syarat omzet/pengalaman); pembingkaian forensik sebagai *"Indikator Risiko Kesamaan Bukti"* per **Pasal 22 UU 5/1999**; PII scrubbing deterministik. |

## Three-minute demo

1. State the user and problem, then disclose that the built-in examples are synthetic.
2. Drag a selection document into the audit form and run the local review.
3. Open a finding and show the source filename/line, evidence, and reviewer note.
4. Explain that a signal requires human verification, record an honest reviewer disposition, and show the review and follow-up draft. The saved label is an audit trail, not proof of model accuracy.
5. Show integration status. Configure credentials only when available; a configured key alone does not prove a working integration.
6. Close with a pilot measurement plan and evidence still to collect: user validation, impact measures, and willingness to pay.

## Evidence to collect before judging

- Short interviews or workflow validation with procurement staff, bidders, or legal reviewers, with consent and no sensitive tender documents.
- A pilot baseline and post-use measurements for review time and reviewer-confirmed signals.
- A supported-file demonstration on the judging machine, plus one fallback case such as an image-only PDF.
- A successful end-to-end integration run if claiming Langflow or Composio is operational; otherwise label it optional/not configured.
- Business model assumptions, pilot costs, and pricing feedback labeled as estimates until validated.
- Attendance, checkpoint, contribution, and team-role evidence for the participation category.

See [Pilot validation protocol](PILOT_VALIDATION.md) for a concrete, non-fabricated measurement plan, privacy gates, and the evidence expected for each rubric category. The dashboard now reports measured local rules-engine runtime only after real audits; this excludes file extraction, external integrations, and reviewer time.
