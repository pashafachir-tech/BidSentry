# BidSentry (v2.1)

BidSentry adalah ruang kerja intelijen pengadaan berbasis *local-first* untuk audit kepatuhan dokumen pengadaan barang/jasa publik di Indonesia (Perpres 16/2018 jo. Perpres 12/2021). Sistem membandingkan persyaratan Kerangka Acuan Kerja (KAK/RKS) dengan bukti penawaran penyedia, merekonsiliasi adendum secara forensik, menghitung simulasi denda keterlambatan, mendeteksi klausul diskriminatif (*brand lock-in*, jadwal mepet, denda tanpa batas, over-budget BoQ), serta menghasilkan draf sanggahan resmi ber-sitasi hukum.

> **Catatan Integritas**: Hasil evaluasi adalah indeks triase risiko untuk membantu pertimbangan manusia (*Human-in-the-Loop*), bukan nasihat hukum formal atau vonis pidana.

---

## 📚 Paket Bukti Rubrik Penilaian Juri

Seluruh dokumen bukti, pengukuran akurasi, dan arsitektur telah disusun lengkap dan transparan:

- 📑 [**Evidence Scorecard (Rubrik Juri)**](file:///d:/bidsentry/docs/EVIDENCE_SCORECARD.md) — Pemetaan terhadap 6 kriteria rubrik (Problem Clarity 20%, Innovation/Monetization 25%, User Impact 15%, Technical Execution & IBM 20%, Responsible AI 10%, Participation 5%).
- 📊 [**Benchmark Results (Dev Set & Blind Test)**](file:///d:/bidsentry/docs/BENCHMARK_RESULTS.md) — Evaluasi akurasi Development Set 24 dokumen (*Baseline: 75.0% ➔ Tuned: 100.0%*) dan Blind Test Set independen 10 dokumen (*Verdict Acc: 70.0%, Trap Evasion: 100.0%*).
- 🧠 [**Model & System Card**](file:///d:/bidsentry/docs/MODEL_CARD.md) — Arsitektur hibrida deterministik vs LLM, kebijakan sensor PII, mitigasi kegagalan, dan batasan operasional.
- 🏗️ [**System Architecture**](file:///d:/bidsentry/docs/ARCHITECTURE.md) — Diagram alir data dan sequence diagram Mermaid, mencakup titik integrasi IBM watsonx / Bob MCP.
- 🔍 [**Competitive Comparison**](file:///d:/bidsentry/docs/COMPETITIVE_COMPARISON.md) — Matriks perbandingan jujur vs Review Manual, Tool Kepatuhan Komersial, dan Chatbot LLM Generik.
- ⚡ [**Status Integrasi IBM watsonx & Bob MCP**](file:///d:/bidsentry/docs/INTEGRATION_STATUS.md) — Laporan live hasil probe skrip verifikasi komponen IBM.
- 👥 [**User Research & Pilot Plan**](file:///d:/bidsentry/docs/INTERVIEW_GUIDE.md) & [**Pilot Results Template**](file:///d:/bidsentry/docs/PILOT_RESULTS_TEMPLATE.md) — Panduan wawancara dan instrumen uji coba (seluruh data manusia berstatus jujur `"BELUM DIKUMPULKAN"`).
- 📝 [**Changelog Iterasi**](file:///d:/bidsentry/docs/CHANGELOG_ITERASI.md) — Catatan riwayat teknis dari Fase 1 hingga Fase 4.

---

## 🚀 Menjalankan Aplikasi di Lingkungan Lokal

Membutuhkan Python 3.11 atau yang lebih baru.

```powershell
# 1. Salin konfigurasi environment
Copy-Item .env.example .env

# 2. Pasang dependensi
pip install -r requirements.txt
pip install openpyxl pyyaml playwright

# 3. Jalankan server lokal
python server.py
```

Buka <http://127.0.0.1:8000> pada peramban. Sistem berjalan langsung tanpa proses kompilasi frontend (*zero build-step*).

---

## 🧪 Verifikasi Pengujian & Benchmark

Juri dan pengembang dapat memverifikasi seluruh komponen secara mandiri melalui perintah berikut:

```powershell
# Jalankan seluruh unit test (53 tests)
pytest tests/ -v

# Jalankan pengujian benchmark Development Set (24 dokumen)
python tests/benchmark_heldout.py

# Jalankan pengujian Blind Test Set independen (10 dokumen tanpa tuning)
python tests/benchmark_blind.py

# Jalankan probe status koneksi IBM watsonx & Bob MCP (Aman / Exit 0)
python scripts/verify_watsonx.py

# Jalankan smoke test UI end-to-end dengan Playwright
python tests/e2e_smoke.py
```

Tangkapan layar hasil evaluasi smoke test tersimpan di [`docs/screenshots/e2e_results.png`](file:///d:/bidsentry/docs/screenshots/e2e_results.png).

---

## 🔒 Keamanan dan Privasi Data

- **Pencegahan DNS Rebinding**: Server membatasi akses pada antarmuka *loopback* (`127.0.0.1`) dan memvalidasi `Host` header secara ketat.
- **Sensor Data Pribadi (PII Masking)**: NIK (16 digit), NPWP, nomor rekening bank, email, dan nomor telepon disensor secara otomatis sebelum payload dikirim ke AI eksternal.
- **Penyimpanan Bebas Teks Asli di Frontend**: Frontend tidak menyimpan kutipan teks dokumen mentah di `localStorage` peramban.
- **Audit Log Atomik**: Penulisan log audit dilakukan secara atomik dengan retensi pembersihan otomatis 90 hari.

---

## 🏛️ Lisensi & Kepatuhan
Sistem dirancang dengan kepatuhan penuh terhadap prinsip etika AI dan regulasi pengadaan barang/jasa publik Republik Indonesia (Perpres No. 12 Tahun 2021).
