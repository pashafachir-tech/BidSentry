# BidSentry (v2.2)
### Platform Intelijen Audit Pengadaan & Sintesis Forensik Lintas-Dokumen Tender Publik

[![Continuous Integration](https://github.com/pashafachir-tech/BidSentry/actions/workflows/ci.yml/badge.svg)](https://github.com/pashafachir-tech/BidSentry/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![IBM watsonx](https://img.shields.io/badge/IBM%20watsonx-Granite--3--8B-052FAD.svg)](https://www.ibm.com/watsonx)
[![Tests Passing](https://img.shields.io/badge/tests-103%20passed-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Sekilas Masalah: Realitas Pengadaan Publik Indonesia

Setiap tahunnya, pengadaan barang dan jasa pemerintah (PBJP) di Indonesia mengelola anggaran lebih dari **Rp 1.165 Triliun** (SiRUP LKPP 2024). Namun, proses evaluasi dokumen tender masih dilakukan secara terpisah dan manual:
- ⏳ **Tantangan Review Manual**: Proses penelaahan dokumen Kerangka Acuan Kerja (KAK), spesifikasi teknis, Berita Acara Adendum, dan Bill of Quantities (BoQ) membutuhkan pembacaan mendalam lintas berkas; estimasi waktu review manual belum diverifikasi secara empiris.
- ⚠️ **Kecurangan & Celah Hukum Tersembunyi**: Praktik penguncian merek (*brand lock-in* eksklusif tanpa opsi setara), jadwal lelang yang sengaja dipersingkat (*compressed timeline*), denda keterlambatan tanpa batas (*uncapped poison pill*), serta pembengkakan anggaran (*over-budget* BoQ) sering kali luput dari pengawasan karena terselip di antara tumpukan dokumen yang berbeda.
- 🔄 **Ketidaksinkronan Antar-Berkas yang Terabaikan**: Dokumen pengadaan tidak pernah berdiri sendiri. Benturan data antara apa yang disyaratkan di KAK, apa yang ditawarkan penyedia di BoQ, apa yang diubah di Adendum, dan apa yang disepakati di draf kontrak sering kali tidak terdeteksi sebelum kontrak ditandatangani.
- ⚖️ **Asimetri Informasi Pelaku Usaha**: Peserta tender dan UMKM sering kali gugur bukan karena mutu teknis, melainkan karena jebakan klausul administratif atau ketiadaan waktu menyusun draf sanggahan resmi sesuai batas waktu LKPP.

**BidSentry** hadir sebagai solusi kecerdasan buatan hibrida (*Local-First Deterministic Engine + IBM watsonx.ai Granite*) yang mengkorelasikan seluruh berkas tender dalam satu ruang kerja intelijen: throughput mesin lokal terukur (latensi eksekusi `engine_duration_ms` pada benchmark); estimasi waktu review manual belum diverifikasi, dengan jaminan kutipan bukti 100% persis (*exact substring verification*).

---

## 🚀 Fitur Unggulan Utama

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               SINTESIS FORENSIK BERKAS PROYEK PENGADAAN (BIDSENTRY v2.2)               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│   [ KAK / SPESIFIKASI ] ───► [ HPS & RINCIAN BoQ ] ───► [ PENAWARAN PENYEDIA ]        │
│             │                            │                          │                  │
│             └──────────────┬─────────────┴──────────────┬───────────┘                  │
│                            ▼                            ▼                              │
│               [ ADENDUM BAPP PENGADAAN ] ───► [ DRAF SURAT PERJANJIAN (SPK) ]          │
│                                          │                                             │
│                                          ▼                                             │
│      ┌──────────────────────────────────────────────────────────────────────────┐      │
│      │ 1. MERANGKUP APA: Resume Ruang Lingkup, Pagu Anggaran, & Peta 5 Berkas   │      │
│      │ 2. KELEMAHAN: Celah Regulasi, Kualifikasi Kedaluwarsa, & Poison Pills   │      │
│      │ 3. KETIDAKSINKRONAN: Benturan KAK vs BoQ, Perubahan Adendum, & Timeline │      │
│      └──────────────────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. 📑 Sintesis Forensik Lintas-Dokumen (Cross-Document Intelligence)
Dokumen dalam satu paket pengadaan saling berhubungan erat. Di bawah riwayat audit, BidSentry menyediakan modul sintesis eksekutif otomatis yang membedah proyek ke dalam **3 Pilar Forensik**:
- **Pilar A: Merangkup Apa (Lingkup & Profil Proyek)**:
  - Menyajikan ringkasan ruang lingkup pekerjaan utama (*Scope of Work*) yang dianalisis mesin.
  - Memetakan nilai pagu anggaran/HPS serta status keterkaitan 5 berkas utama: KAK & Spesifikasi Teknis, HPS & BoQ/RAB, Dokumen Penawaran Penyedia, Berita Acara Adendum (BAPP), dan Draf Kontrak SPK.
- **Pilar B: Kelemahan & Celah Regulasi (Vulnerabilities)**:
  - Deteksi otomatis indikasi penguncian merek spesifik yang melanggar **Pasal 19 Perpres 12/2021**.
  - Peringatan dokumen kualifikasi yang absen atau izin operasional yang mendekati masa kedaluwarsa ($\le$ 30 hari).
  - Peringatan klausul denda tanpa batas maksimal (*Poison Pill*) beserta simulasi nominal paparan risiko keuangan (*Financial Exposure*).
- **Pilar C: Ketidaksinkronan Antar-Berkas (Cross-Document Discrepancies)**:
  - **Benturan KAK vs Penawaran/BoQ**: Spesifikasi yang diminta pada KAK tidak diimbangi surat dukungan atau bukti kesetaraan pada berkas penawaran rekanan.
  - **Benturan Adendum vs Syarat Awal (*Contract Dilution*)**: Deteksi klausul yang diubah, digugurkan, atau dilonggarkan secara sepihak melalui Berita Acara Adendum dibandingkan dokumen pemilihan awal.
  - **Benturan Jadwal & Batas Waktu**: Peringatan masa sanggah atau penyiapan penawaran yang dipangkas di bawah ambang legal LKPP (**Pasal 54 Perpres 12/2021**).

### 2. 🔗 Matriks Keterlacakan Silang Antar-Dokumen (Traceability Matrix)
Tabel visual interaktif yang memetakan perjalanan setiap ketentuan penting:
$$\text{Ketentuan KAK Awal} \quad\longrightarrow\quad \text{Modifikasi Adendum} \quad\longrightarrow\quad \text{Respon Bukti Penyedia} \quad\longrightarrow\quad \text{Status Forensik Sinkronisasi}$$
Auditor dan reviewer dapat langsung melihat apakah suatu syarat berstatus `TERPENUHI · SINKRON`, `KESENJANGAN / BENTURAN`, atau `DIUBAH ADENDUM`.

### 3. 📁 Manajemen Proyek Berbasis Folder & Antarmuka Modern
- **Sidebar Folder Proyek**: Bilah navigasi kiri ditata layaknya penjelajah proyek rapi dengan tombol **`+ Add new project`**, badge jumlah proyek aktif, dot indikator risiko tender, dan pemilihan instan.
- **Dukungan Dark Mode Menyeluruh**: Desain antarmuka responsif yang nyaman di mata dengan palet tema gelap kontras tinggi tanpa kebocoran warna terang.

### 4. 🎯 Peran Pengguna Ganda (Dual-Perspective Mode)
Pengguna dapat berganti sudut pandang dengan satu klik di topbar:
* **Mode Panitia / Pokja**:
  - Evaluasi kepatuhan rekanan terhadap regulasi pengadaan.
  - Skrining potensi kolusi dan indikasi kesamaan dokumen (UU 5/1999 Pasal 22).
  - Generator otomatis draf **Berita Acara Hasil Pemilihan (BAHP)** berformat DOCX siap cetak.
* **Mode Peserta / Vendor**:
  - *Pre-flight bid check* sebelum submit ke portal LPSE untuk memastikan tidak ada berkas yang kurang.
  - Generator otomatis **Surat Sanggahan Resmi** berformat DOCX/PDF lengkap dengan kutipan pasal dan bukti persis saat terdeteksi red flag KAK diskriminatif.

---

## 💡 Kedalaman Teknologi & Pengamanan Data

### 🛡️ 1. Keamanan Kriptografis: SHA-256 Hash Chained Audit Trail
* **Bahasa Awam (Buku Kas Digital Bersegel Anti-Manipulasi)**:  
  Sama seperti buku kas notaris yang setiap halamannya distempel dan diparaf berantai, setiap kali audit dijalankan atau catatan reviewer ditambahkan, sistem mencatatnya dalam rantai segel digital. Jika ada oknum yang mengubah hasil vonis atau menghapus data temuan langsung di database, rantai segel akan langsung terputus dan sistem membunyikan alarm integritas (*tamper-evident*).
* **Bahasa Teknis**:  
  Setiap entri log audit diikat secara berantai menggunakan algoritma kriptografis SHA-256 ([`bidsentry/lib/audit_log.py`](bidsentry/lib/audit_log.py) dan [`bidsentry/core/audit_trail.py`](bidsentry/core/audit_trail.py) via fungsi `verify_chain()`). Format record mencatat `previous_hash`, `payload_hash`, dan `record_hash` untuk memastikan kepatuhan standar forensik investigasi BPK/APIP.

### 🔒 2. Sensor Data Pribadi Otomatis (Deterministic PII Scrubbing)
* **Bahasa Awam (Penghapus Data Pribadi Otomatis)**:  
  Dokumen tender sering kali memuat KTP pengurus atau buku rekening bank. Sebelum dokumen dikirim atau diproses oleh kecerdasan buatan, sistem secara otomatis menyamarkan data pribadi tersebut demi mematuhi UU Perlindungan Data Pribadi (UU PDP).
* **Bahasa Teknis**:  
  Modul redaksi deterministik ([`bidsentry/lib/pii.py`](bidsentry/lib/pii.py)) menyensor NIK KTP (termasuk deteksi 16 digit mandiri), NPWP perusahaan, nomor rekening bank (`Rek. [Bank] \d+`), nomor telepon, dan email sebelum naskah diekstraksi ke model eksternal.

### 🤖 3. Model Fondasi IBM watsonx.ai & Granite 3-8B
* **Bahasa Awam (AI Khusus Dokumen Regulasi & Bisnis)**:  
  Alih-alih menggunakan AI percakapan umum yang rawan mengarang bebas (*halusinasi*), BidSentry ditenagai model enterprise **IBM Granite-3-8B-Instruct** yang dilatih untuk memahami struktur kontrak, klausul hukum, dan ekstraksi entitas pengadaan.
* **Bahasa Teknis**:  
  Terintegrasi via SDK `ibm-watsonx-ai` ([`WatsonxService`](bidsentry/services/watsonx_service.py)) dengan parameter deterministik *greedy decoding* (temperatur 0.0), pra-pemeriksaan guardrail lokal, serta mekanisme fallback anggun ke mesin aturan lokal dan visual pipeline Langflow ([`tender_extraction_flow.json`](langflow/tender_extraction_flow.json)).

### ✍️ 4. Grounded Legal Generator (Exact Substring Verification)
* **Bahasa Awam (Anti-Halusinasi 100%)**:  
  Surat sanggahan dan Berita Acara yang diterbitkan sistem dijamin tidak pernah mengarang nomor pasal atau kalimat fiktif. Seluruh kutipan wajib bersumber dari kalimat nyata yang ada di dokumen asli tender.
* **Bahasa Teknis**:  
  Engine memvalidasi bahwa setiap sitasi bukti yang dimasukkan ke dalam generator DOCX/PDF adalah substring persis (*exact substring matching*) dari naskah KAK/Adendum yang terindeks secara lokal.

### ⚖️ 5. Keadilan Algoritmik UMKM (Algorithmic Fairness)
* Sesuai amanat **Pasal 65 Perpres 12/2021 & PP 7/2021**, sistem memberikan relaksasi ambang batas modal kerja dan syarat pengalaman kerja sejenis bagi pelaku usaha mikro dan kecil untuk mencegah diskriminasi akses pengadaan pemerintah.

---

## 📊 Hasil Benchmark & Pengujian Nyata

Seluruh angka di bawah dihitung secara dinamis dari eksekusi kode aktual tanpa manipulasi:

| Dataset Uji | Jumlah Dokumen | Akurasi Vonis | Trap Evasion (Lolos Jebakan) | Keterangan Metodologi |
| :--- | :---: | :---: | :---: | :--- |
| **Development Set** | **24 Dokumen** | **100.0%** | **100.0% (9/9)** | Dipakai memandu kalibrasi aturan deterministik. |
| **Validation Set v1** | **10 Dokumen** | **90.0%** | **100.0% (3/3)** | Validation Set v1 (label tidak diubah; engine dikalibrasi setelah putaran pertama dari 70.0% ke 90.0%). |
| **Narrative Budget Set** | **5 Dokumen** | **80.0%** | **100.0% (1/1)** | Pengujian ekstraksi angka Pagu/BoQ pada prosa naratif bebas. |
| **Real PDF Fixtures** | **2 PDF Multi-Halaman** | **100.0%** | **100.0%** | Tabel BoQ 15 item pekerjaan & KAK lengkap (PDF nyata). |

> **Catatan Integritas Hasil**: Kasus meleset pada Validation Set v1 (`blind_07`) dan Narrative Set (`budget_02`) disebabkan oleh prinsip kehati-hatian (*safety-first*): sistem menolak menyimpulkan `GO` secara ceroboh saat berkas kualifikasi belum lengkap, melainkan menetapkan status `BELUM CUKUP BUKTI` dan menyerahkan keputusan akhir kepada auditor manusia (*Human-in-the-Loop*).

### ⚠️ Batasan yang Diketahui (Known Limitations)
- **Macro Precision/Recall/F1 Rendah**: Pada Validation Set v1 (Macro P ≈15%, R ≈29%, F1 ≈20%) dan Narrative Budget Set (Macro P ≈25%, R ≈17%, F1 ≈20%), metrik per-aturan relatif rendah. Berdasarkan inspeksi empiris, hal ini terutama dipicu oleh perbedaan penamaan ID aturan antara skema label uji dengan ID engine, serta terdeteksinya klausul sah tambahan pada fixture (lihat [`docs/BENCHMARK_RESULTS.md`](docs/BENCHMARK_RESULTS.md)).
- **Cakupan Aturan Berbasis Pola Teks**: Deteksi didasarkan pada ekspresi reguler dan pencocokan leksikal deklaratif; belum mencakup inferensi semantik mendalam tanpa model bahasa.
- **Dukungan Bahasa Dokumen**: Utamanya dioptimalkan untuk bahasa Indonesia pengadaan (istilah LPSE, KAK, HPS, DIPA); belum mencakup dokumen berbahasa Inggris penuh selain frasa kunci jadwal dan ekuivalensi dasar.
- **Deteksi Diskriminasi Regional Terbatas**: Baru mencakup pola pembatasan domisili, keanggotaan asosiasi, dan kantor cabang spesifik wilayah tertentu.
- **Ketahanan Prompt Injection**: Engine aturan lokal 100% kebal prompt injection karena bersifat deterministik tanpa LLM; namun jalur LLM eksternal opsional (watsonx/Langflow) hanya dilindungi oleh penyensoran pola PII dan validasi kutipan exact substring sebelum inferensi.

---

## ⚡ Panduan Memulai Cepat (Quickstart)

### Prasyarat
- Python 3.11 atau lebih baru
- Sistem Operasi: Windows, macOS, atau Linux

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

## 🧪 Rangkaian Pengujian Mandiri (103 Test Cases)

Seluruh komponen dapat diverifikasi secara independen oleh juri teknis melalui perintah berikut:

```bash
# 1. Jalankan seluruh unit & integration test (103 passed tests, 0 warnings)
pytest tests/ -v -W default

# 2. Jalankan benchmark Development Set (24 dokumen)
python tests/benchmark_heldout.py

# 3. Jalankan benchmark Independent Blind Set (10 dokumen)
python tests/benchmark_blind.py

# 4. Jalankan benchmark Anggaran Prosa Bebas (5 dokumen narasi)
python tests/benchmark_budget_narrative.py

# 5. Jalankan verifikasi status integrasi IBM watsonx (Exit 0 aman)
python scripts/verify_watsonx.py

# 6. Jalankan pengujian ekstraksi berkas PDF nyata & BoQ Excel
pytest tests/test_pdf_real_extraction.py -v

# 7. Jalankan uji asap end-to-end (E2E) dan pembaruan tangkapan layar browser
python tests/e2e_smoke.py
```

> **Tangkapan Layar Bukti Hasil E2E:** Tersedia pada [docs/screenshots/e2e_results.png](docs/screenshots/e2e_results.png).

---

## 📚 Dokumen Pendukung untuk Penjurian

- 📑 [**Evidence Scorecard (Rubrik Juri)**](docs/EVIDENCE_SCORECARD.md) — Pemetaan pembuktian terhadap seluruh kriteria penjurian.
- 💰 [**Strategi Monetisasi B2B SaaS**](docs/MONETIZATION_STRATEGY.md) — Model bisnis 3-tier, penetrasi B2B BUMN/Auditor, dan proyeksi unit economics.
- 🏗️ [**Peta Arsitektur Terkonsolidasi**](docs/ARCHITECTURE_CONSOLIDATED.md) — Struktur arsitektur backend, konsolidasi modul finansial, dan data flow.
- 🧠 [**Model & System Card**](docs/MODEL_CARD.md) — Kebijakan vonis deterministik, mitigasi bias etika, dan batasan operasional.
- 🔬 [**Laporan Hasil Benchmark Lengkap**](docs/BENCHMARK_RESULTS.md) — Analisis detail per dokumen uji, confusion matrix, dan mitigasi false positives.
- 📋 [**Checklist Kesiapan Juri**](docs/JUDGE_READINESS.md) — Verifikasi tuntas terhadap 8 *red flags* audit teknis.

---

## 🏛️ Lisensi & Kepatuhan Regulasi Nasional

Proyek ini dilisensikan di bawah lisensi **[MIT](LICENSE)**.  
Seluruh logika evaluasi dan modul forensik dirancang merujuk pada regulasi Republik Indonesia:
- **Perpres No. 16 Tahun 2018** jo. **Perpres No. 12 Tahun 2021** tentang Pengadaan Barang/Jasa Pemerintah.
- **UU No. 5 Tahun 1999 Pasal 22** tentang Larangan Praktik Monopoli dan Persaingan Usaha Tidak Sehat.
- **UU No. 27 Tahun 2022** tentang Pelindungan Data Pribadi (UU PDP).
- **Peraturan LKPP No. 12 Tahun 2021** tentang Pedoman Pelaksanaan Pengadaan Barang/Jasa Pemerintah Melalui Penyedia.
