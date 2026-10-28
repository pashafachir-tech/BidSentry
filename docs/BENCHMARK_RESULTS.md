# Laporan Evaluasi Akurasi & Benchmark BidSentry

> **Pernyataan Integritas Metodologi**:
> Laporan ini memisahkan secara tegas tiga dataset evaluasi independen:
> 1. **Dataset Pengembangan & Penyetelan (Development Set — 24 Dokumen)**: Digunakan untuk memandu dekopling aturan dan verifikasi regresi pola.
> 2. **Dataset Validasi Independen v1 (Validation Set v1 — 10 Dokumen)**: Dilabeli secara independen sebelum dievaluasi, dibekukan (*frozen*), dan dijalankan tanpa pengubahan label (*zero-tuning*), untuk mengukur generalisasi obyektif sistem.
> 3. **Dataset Anggaran Narasi Bebas (Narrative Budget Test Set — 5 Dokumen Baru)**: Dokumen pengujian terpisah yang ditulis setelah penyempurnaan parser anggaran untuk menguji ketahanan ekstraksi angka Pagu DIPA dan BoQ/HPS pada prosa bebas non-tabel.

---

## BAGIAN I: Dataset Pengembangan (Development Set — 24 Dokumen)

Dataset ini terdiri dari 24 dokumen sintetis yang memodelkan skenario pelanggaran dan klausul jebakan umum sesuai Perpres 12/2021.

### 1. Perbandingan Sebelum vs Sesudah Penyetelan Engine

| Metrik Evaluasi | Baseline Awal (Commit `f094ef8`) | Pasca-Penyetelan (Commit `369b3a3`) | Delta Perubahan | Keterangan Evaluasi |
|---|---:|---:|---:|---|
| **Verdict Accuracy** | 75.0% (18/24) | **100.0%** (24/24) | **+25.0%** | Perbaikan status default `TIDAK ADA SYARAT TERBACA` |
| **Trap Evasion Rate** | 77.8% (7/9) | **100.0%** (9/9) | **+22.2%** | Eliminasi false positive klausul kesetaraan & pakta integritas |
| **Macro Precision** | 82.1% | **100.0%** | **+17.9%** | Seluruh 14 aturan terkalibrasi tanpa over-triggering |
| **Macro Recall** | 89.3% | **100.0%** | **+10.7%** | Rekonstruksi kalimat lintas baris (*cross-line stitching*) |
| **Macro F1 Score** | 85.6% | **100.0%** | **+14.4%** | Keseimbangan deteksi red flag dan perlindungan klausul sah |

> **Catatan Koreksi Penulisan Kasus Jebakan**:
> Penyebut riil pada dataset `data/benchmark/` adalah **9 kasus jebakan** (`doc_01`, `03`, `06`, `08`, `10`, `12`, `16`, `21`, `23`), dan kode evaluator mengonfirmasi 9 dari 9 jebakan berhasil dievasi (100.0%).

### 2. Batasan Metodologi Development Set
Karena 24 dokumen ini digunakan oleh tim teknis selama proses refaktorisasi `engine.py` dan `config/rules.yaml`, skor 100.0% pada set ini mengukur **tingkat kepatuhan implementasi kode terhadap spesifikasi kasus uji yang dirancang**, BUKAN bukti bahwa sistem sempurna pada semua dokumen pengadaan di dunia nyata.

---

## BAGIAN II: Evaluasi Validasi Independen (Validation Set v1 — 10 Dokumen Frozen)

Untuk menguji kemampuan generalisasi sistem secara jujur, 10 dokumen uji di `data/test_blind/` mencakup variasi pengadaan konstruksi, TI, jasa kebersihan, alat kesehatan, sewa kendaraan, dan dokumen non-standar. Label dokumen ini **dibekukan** dan tidak disentuh.

### 1. Ringkasan Hasil Validasi Independen (Zero-Tuning)

- **Tanggal Pengujian:** 2026-10-28
- **Skrip Evaluator:** `tests/benchmark_blind.py`
- **Total Dokumen Uji:** 10 Dokumen Independen
- **Verdict Accuracy:** **90.0%** (9 dari 10 dokumen terklasifikasi tepat)
- **Trap Evasion Rate:** **100.0%** (3 dari 3 skenario jebakan lolos tanpa false alarm)
- **Macro Precision:** 16.0%
- **Macro Recall:** 30.8%
- **Macro F1 Score:** 21.1%

### 2. Detail Hasil per Dokumen Validasi v1

| ID Dokumen | Judul Skenario Uji | Expected Verdict | Actual Verdict | Status Evaluasi | Keterangan Kasus |
|---|---|---|---|:---:|---|
| `blind_01` | Rehabilitasi Gedung Kantor (Patuh & Bersih) | `GO` | `GO` | **MATCH** | Memenuhi seluruh syarat administratif & teknis |
| `blind_02` | Laptop Mobilitas (Lock-in Intel Core Ultra) | `NO-GO` | `NO-GO` | **MATCH** | Berhasil mendeteksi penguncian CPU Intel tanpa opsi setara |
| `blind_03` | Kajian Tata Ruang (Jadwal Sangat Mepet) | `NO-GO` | `NO-GO` | **MATCH** | Berhasil menangkap penawaran 4 hari & sanggah 2 hari |
| `blind_04` | CT-Scan RSUD (Denda Keterlambatan Tanpa Batas) | `NO-GO` | `NO-GO` | **MATCH** | Berhasil mendeteksi klausul denda tanpa batas maksimal |
| `blind_05` | Jasa Kebersihan (Pakta Integritas Bebas KKN) | `GO` | `GO` | **MATCH (TRAP)** | Jebakan komitmen integritas normatif lolos tanpa alarm |
| `blind_06` | Jasa ERP (Total BoQ Melebihi Pagu Anggaran) | `NO-GO` | `NO-GO` | **MATCH** | Parser anggaran narasi berhasil mendeteksi defisit BoQ vs Pagu |
| `blind_07` | Sewa Kendaraan Dinas (Spesifikasi Merek + Setara) | `GO` | `NO-GO` | **MISMATCH** | **False Positive Verdict**: Klausul merek setara lolos (Trap: PASS), tetapi dokumen minim slot berkas memicu gap administratif |
| `blind_08` | Meubeler Kantor (SBU Kedaluwarsa < 30 Hari) | `BELUM CUKUP BUKTI` | `BELUM CUKUP BUKTI` | **MATCH** | Kebijakan verdict baru mengalihkan expiring SBU ke status bukti terpisah |
| `blind_09` | Konsultan Jalan (Billing Rate di Atas INKINDO) | `NO-GO` | `NO-GO` | **MATCH** | Berhasil mendeteksi mark-up tarif tenaga ahli Rp 140 jt/bln |
| `blind_10` | Notulensi Koordinasi (Format Narasi Lepas) | `TIDAK ADA SYARAT TERBACA` | `TIDAK ADA SYARAT TERBACA` | **MATCH (TRAP)** | Berhasil mendeteksi ketiadaan bab syarat teknis |

---

## BAGIAN III: Evaluasi Dataset Anggaran Narasi Bebas (Narrative Budget Test Set — 5 Dokumen Baru)

Dataset baru di `data/test_narrative_budget/` disusun khusus untuk menguji kemampuan ekstraksi angka anggaran (Pagu DIPA, BoQ, dan HPS) dalam bentuk kalimat prosa bebas tanpa format tabel spreadsheet.

### 1. Ringkasan Hasil Uji Anggaran Narasi Bebas

- **Tanggal Pengujian:** 2026-10-28
- **Skrip Evaluator:** `tests/benchmark_budget_narrative.py`
- **Total Dokumen Uji:** 5 Dokumen Baru
- **Verdict Accuracy:** **80.0%** (4 dari 5 dokumen terklasifikasi tepat)
- **Trap Evasion Rate:** **100.0%** (1 dari 1 kasus jebakan lolos tanpa false alarm)
- **Macro Precision:** 25.0%
- **Macro Recall:** 25.0%
- **Macro F1 Score:** 25.0%

### 2. Detail Hasil per Dokumen Anggaran Narasi

| ID Dokumen | Judul Skenario Uji | Expected Verdict | Actual Verdict | Status Evaluasi | Keterangan Kasus |
|---|---|---|---|:---:|---|
| `budget_01` | Pengadaan ERP Prosa BoQ > Pagu DIPA | `NO-GO` | `NO-GO` | **MATCH** | Berhasil menangkap Pagu Rp 5 M vs BoQ Rp 6,25 M |
| `budget_02` | Layanan Jaringan Komunikasi (Biaya Sesuai Pagu) | `GO` | `BELUM CUKUP BUKTI` | **MISMATCH** | Biaya valid (Trap PASS), namun ketiadaan slot bukti NIB/NPWP memicu status bukti |
| `budget_03` | Server Storage HPS Prosa > Pagu DIPA | `NO-GO` | `NO-GO` | **MATCH** | Berhasil menangkap Pagu Rp 3 M vs HPS Rp 3,4 M |
| `budget_04` | Pedoman Normatif HPS Tidak Boleh > Pagu (Trap) | `GO` | `GO` | **MATCH (TRAP)** | Kalimat normatif undang-undang tidak memicu false alarm |
| `budget_05` | Modernisasi Data Center Rekap Biaya > Pagu | `NO-GO` | `NO-GO` | **MATCH** | Berhasil menangkap Pagu Rp 10 M vs Biaya Rp 12,8 M |

---

## BAGIAN IV: Analisis Kegagalan & Area Kelemahan Engine (Error Analysis)

Evaluasi jujur terhadap dokumen mismatch:

1. **Interaksi Multi-Slot Dokumen (Kasus `blind_07` & `budget_02`)**:
   - *Masalah*: Dokumen pengujian hanya melampirkan teks KAK/Draf Kontrak tanpa melampirkan bukti penyedia (slot NIB, NPWP kosong). Sesuai kebijakan verdict deterministik yang ketat, ketiadaan bukti dokumen legalitas memicu evaluasi administratif yang menurunkan verdict menjadi `BELUM CUKUP BUKTI` atau `NO-GO` jika syarat wajib tidak terpenuhi.
   - *Rekomendasi Arsitektur*: Mendukung dua sakelar evaluasi: mode "Audit KAK Saja" (hanya memindai diskriminasi dokumen lelang) vs mode "Audit Tender Lengkap" (mencakup kepatuhan berkas penawaran penyedia).

---

## BAGIAN V: Cara Menjalankan Ulang Seluruh Benchmark

```powershell
# 1. Jalankan benchmark Development Set (24 dokumen)
python tests/benchmark_heldout.py

# 2. Jalankan benchmark Validation Set v1 Independen (10 dokumen)
python tests/benchmark_blind.py

# 3. Jalankan benchmark Narrative Budget Test Set Baru (5 dokumen)
python tests/benchmark_budget_narrative.py
```
