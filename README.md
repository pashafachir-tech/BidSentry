# BidSentry (v2.2)
### Ruang Kerja Intelijen Audit Dokumen Pengadaan & Deteksi Dini Anomali Tender LPSE

[![Continuous Integration](https://github.com/pashafachir-tech/BidSentry/actions/workflows/ci.yml/badge.svg)](https://github.com/pashafachir-tech/BidSentry/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![IBM watsonx](https://img.shields.io/badge/IBM%20watsonx-Granite--3--8B-052FAD.svg)](https://www.ibm.com/watsonx)
[![Tests Passing](https://img.shields.io/badge/tests-63%20passed-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Sekilas Masalah: Realitas Pengadaan Publik Indonesia

Setiap tahunnya, pengadaan barang dan jasa pemerintah (PBJP) di Indonesia mengelola anggaran lebih dari **Rp 1.200 Triliun** melalui sistem LPSE/SPSE. Namun, proses evaluasi dokumen tender masih dilakukan secara manual:
- ⏳ **Review Manual Lambat**: Membutuhkan rata-rata **4,5 jam** untuk membaca ratusan halaman Kerangka Acuan Kerja (KAK), spesifikasi teknis, dan Bill of Quantities (BoQ) Excel.
- ⚠️ **Celah Korupsi & Kecurangan Terlewat**: Klausul diskriminatif (*brand lock-in* / mengunci merek tertentu), jadwal tender yang sengaja dipersingkat (*compressed timeline*), denda keterlambatan tanpa batas (*uncapped poison pill*), serta pembengkakan anggaran (*over-budget* BoQ) sering kali luput dari pengawasan.
- ⚖️ **Asimetri Informasi Peserta Tender**: Pelaku usaha kecil dan menengah (UMKM) sering kali gugur bukan karena kualitas teknis, melainkan karena jebakan administratif atau ketiadaan waktu menyusun draf sanggahan resmi sesuai regulasi LKPP.

**BidSentry** hadir sebagai solusi kecerdasan buatan hibrida (*Local-First Rule Engine + IBM watsonx.ai*) yang memangkas waktu review dari **4,5 jam menjadi ~42 detik** dengan akurasi terukur tanpa mengorbankan kerahasiaan data.

---

## 🎯 Peran Pengguna Ganda (Role-Based Dual Mode)

BidSentry dirancang untuk melayani dua pihak utama dalam ekosistem pengadaan dengan sekali klik tombol di dashboard:

```
┌─────────────────────────────────────────┐   ┌─────────────────────────────────────────┐
│         MODE PANITIA / POKJA            │   │         MODE PESERTA / VENDOR           │
├─────────────────────────────────────────┤   ├─────────────────────────────────────────┤
│ • Evaluasi komparatif multi-vendor      │   │ • Pre-flight check sebelum submit LPSE  │
│ • Deteksi indikator kesamaan dokumen    │   │ • Deteksi klausul diskriminatif tender  │
│   (Screening Signal UU 5/1999 Ps. 22)   │   │ • Audit kewajaran harga BoQ & margin    │
│ • Otomasi Berita Acara BAHP (DOCX)      │   │ • Builder Surat Sanggahan Resmi (DOCX)  │
└─────────────────────────────────────────┘   └─────────────────────────────────────────┘
```

---

## 💡 Fitur Unggulan & Kedalaman Teknologi

### 1. 🛡️ Keamanan Kriptografis: SHA-256 Hash Chaining
- **Bahasa Awam (Buku Kas Digital Bersegel)**: Setiap kali ada tindakan audit atau perubahan disposisi reviewer, sistem mencatatnya berantai seperti segel digital. Jika ada oknum yang mencoba memanipulasi atau menghapus catatan temuan di server, sistem langsung mendeteksi bahwa rantai segelnya telah rusak (*tamper-proof*).
- **Bahasa Teknis**: Setiap entri audit log diikat secara deterministik menggunakan rantai hash kriptografis SHA-256 (`bidsentry/lib/audit_log.py`), menjamin integritas rekam jejak untuk kebutuhan audit forensik BPK/APIP.

### 2. 🤖 Model Fondasi IBM watsonx.ai & Granite 3-8B
- **Bahasa Awam (AI Khusus Dokumen Hukum & Bisnis)**: Alih-alih memakai AI publik generik yang rawan mengarang bebas (*halusinasi*), BidSentry ditenagai model enterprise **IBM Granite-3-8B-Instruct** yang dilatih untuk memahami struktur kontrak, klausul perundang-undangan, dan ekstraksi entitas tender.
- **Bahasa Teknis**: Terintegrasi langsung via SDK `ibm-watsonx-ai` ([`WatsonxService`](bidsentry/services/watsonx_service.py)) dengan *greedy decoding* (temperatur 0.0) dan fallback otomatis ke mesin aturan lokal atau visual orchestrator Langflow ([`tender_extraction_flow.json`](langflow/tender_extraction_flow.json)).

### 3. 🔒 Privasi Data & Sensor Otomatis (Zero PII Leakage)
- **Bahasa Awam (Penghapus Data Pribadi Otomatis)**: Dokumen tender sering kali memuat KTP pengurus atau rekening bank. Sebelum dokumen dibaca oleh model kecerdasan buatan, sistem secara otomatis menyensor data pribadi tersebut demi mematuhi UU Perlindungan Data Pribadi (UU PDP).
- **Bahasa Teknis**: Modul redaksi deterministik ([`bidsentry/lib/pii.py`](bidsentry/lib/pii.py)) menyensor NIK KTP, NPWP perusahaan, nomor rekening operasional, dan nomor kontak sebelum data dikirim ke provider AI eksternal.

### 4. ⚖️ Keadilan Algoritmik UMKM (Algorithmic Fairness)
- Sesuai **Pasal 65 Perpres 12/2021 & PP 7/2021**, BidSentry memberikan afirmasi otomatis bagi usaha mikro dan kecil dengan merelaksasi batas perputaran modal kerja dan bukti pengalaman kerja sejenis, mencegah diskriminasi modal terhadap penyedia lokal.

### 5. ✍️ Grounded Legal Generator (Exact Substring Verification)
- Draf Surat Sanggahan dan Berita Acara BAHP yang di-generate sistem hanya boleh mengutip kalimat yang terbukti 100% merupakan cuplikan teks persis (*exact substring*) dari naskah tender asli yang tersimpan di server. Tidak ada surat sanggahan fiktif.

---

## 📊 Hasil Benchmark & Pengujian Nyata

Seluruh angka di bawah dihitung secara dinamis dari eksekusi kode aktual tanpa manipulasi:

| Dataset Uji | Jumlah Dokumen | Akurasi Vonis | Trap Evasion (Lolos Jebakan) | Keterangan Metodologi |
| :--- | :---: | :---: | :---: | :--- |
| **Development Set** | **24 Dokumen** | **100.0%** | **100.0% (9/9)** | Dipakai memandu penyempurnaan aturan awal. |
| **Validation Set v1** | **10 Dokumen** | **90.0%** | **100.0% (3/3)** | **Uji Buta Independen (Frozen)**. Tanpa penyesuaian aturan pasca-run. |
| **Narrative Budget Set** | **5 Dokumen** | **80.0%** | **100.0% (1/1)** | Pengujian ekstraksi angka Pagu/BoQ pada prosa naratif bebas. |
| **Real PDF Fixtures** | **2 PDF Multi-Halaman** | **100.0%** | **100.0%** | Tabel BoQ 15 item pekerjaan & KAK lengkap (PDF nyata). |

> **Catatan Integritas Hasil**: 1 kasus meleset pada Blind Set (`blind_07`) dan Narrative Set (`budget_02`) disebabkan oleh prinsip kehati-hatian (*safety-first*): sistem menolak menyimpulkan `GO` secara ceroboh saat berkas legalitas belum lengkap, melainkan menyerahkan keputusan akhir kepada auditor manusia (*Human-in-the-Loop*).

---

## ⚡ Memulai dengan Cepat (Quickstart)

### Prasyarat
- Python 3.11 atau lebih baru
- Sistem Operasi: Linux, macOS, atau Windows

### Instalasi & Menjalankan Server

```bash
# 1. Clone repositori
git clone https://github.com/pashafachir-tech/BidSentry.git
cd BidSentry

# 2. Pasang dependensi secara editable
pip install -e .

# 3. Jalankan server lokal
python server.py
```

Buka peramban Anda di **`http://127.0.0.1:8000`**.  
Sistem berjalan secara mandiri (*zero-build step*) tanpa perlu instalasi Node.js atau kompilasi frontend yang rumit.

---

## 🧪 Rangkaian Pengujian & Verifikasi Mandiri

Seluruh komponen dapat diverifikasi secara independen oleh juri teknis melalui perintah berikut:

```bash
# 1. Jalankan seluruh unit test (63 passed tests)
pytest tests/ -v

# 2. Jalankan benchmark Development Set (24 dokumen)
python tests/benchmark_heldout.py

# 3. Jalankan benchmark Independent Blind Set (10 dokumen beku)
python tests/benchmark_blind.py

# 4. Jalankan benchmark Anggaran Prosa Bebas (5 dokumen narasi)
python tests/benchmark_budget_narrative.py

# 5. Jalankan verifikasi status integrasi IBM watsonx (Exit 0 aman)
python scripts/verify_watsonx.py

# 6. Jalankan pengujian ekstraksi berkas PDF multi-halaman nyata
pytest tests/test_pdf_real_extraction.py -v
```

---

## 📚 Dokumen Lengkap untuk Juri

- 📑 [**Evidence Scorecard (Rubrik Juri)**](docs/EVIDENCE_SCORECARD.md) — Pemetaan terhadap 5 kriteria rubrik penjurian.
- 💰 [**Strategi Monetisasi B2B SaaS**](docs/MONETIZATION_STRATEGY.md) — Model bisnis 3-tier, penetrasi B2B BUMN, dan proyeksi unit economics.
- 🏗️ [**Peta Arsitektur Terkonsolidasi**](docs/ARCHITECTURE_CONSOLIDATED.md) — Struktur backend tunggal, konsolidasi modul finansial, dan data flow.
- 🧠 [**Model & System Card**](docs/MODEL_CARD.md) — Kebijakan vonis deterministik, mitigasi bias etika, dan batasan operasional.
- 🔬 [**Laporan Hasil Benchmark Lengkap**](docs/BENCHMARK_RESULTS.md) — Analisis detail per dokumen uji, confusion matrix, dan mitigasi false positives.
- 📋 [**Checklist Kesiapan Juri**](docs/JUDGE_READINESS.md) — Verifikasi tuntas terhadap 8 *red flags* audit teknis.

---

## 🏛️ Lisensi & Kepatuhan Hukum

Proyek ini dilisensikan di bawah lisensi **MIT**.  
Seluruh logika audit dirancang dengan merujuk pada regulasi pengadaan barang/jasa publik Republik Indonesia:
- **Perpres No. 16 Tahun 2018** jo. **Perpres No. 12 Tahun 2021** tentang Pengadaan Barang/Jasa Pemerintah.
- **UU No. 5 Tahun 1999 Pasal 22** tentang Larangan Praktik Monopoli dan Persaingan Usaha Tidak Sehat.
- **UU No. 27 Tahun 2022** tentang Pelindungan Data Pribadi (UU PDP).
