# Laporan Evaluasi Akurasi & Benchmark BidSentry

> **Pernyataan Integritas Metodologi**:
> Laporan ini memisahkan secara tegas dua dataset evaluasi:
> 1. **Dataset Pengembangan & Penyetelan (Development & Tuning Set — 24 Dokumen)**: Digunakan untuk memandu dekopling aturan dan verifikasi regresi pola.
> 2. **Dataset Uji Buta Independen (Blind Test Set — 10 Dokumen)**: Dilabeli secara independen sebelum dievaluasi, dijalankan tanpa penyesuaian aturan (*zero-tuning*), untuk mengukur generalisasi obyektif sistem.

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

> **Catatan Koreksi Penulisan**:
> Pada log ringkasan sebelumnya tercatat angka `8/8` untuk Trap Evasion pasca-perbaikan. Ini merupakan kekeliruan ketik (*clerical typo*) pada templat teks tabel pembanding; penyebut riil pada dataset `data/benchmark/` adalah **9 kasus jebakan** (`doc_01`, `03`, `06`, `08`, `10`, `12`, `16`, `21`, `23`), dan kode evaluator mengonfirmasi 9 dari 9 jebakan berhasil dievasi (100.0%).

### 2. Batasan Metodologi Development Set
Karena 24 dokumen ini digunakan oleh tim teknis selama proses refaktorisasi `engine.py` dan `config/rules.yaml`, skor 100.0% pada set ini mengukur **tingkat kepatuhan implementasi kode terhadap spesifikasi kasus uji yang dirancang**, BUKAN bukti bahwa sistem sempurna pada semua dokumen pengadaan di dunia nyata.

---

## BAGIAN II: Evaluasi Uji Buta Independen (Blind Test Set — 10 Dokumen)

Untuk menguji kemampuan generalisasi sistem secara jujur, dibuat 10 dokumen uji baru di `data/test_blind/` yang mencakup variasi pengadaan konstruksi, TI, jasa kebersihan, alat kesehatan, sewa kendaraan, dan dokumen non-standar. Dokumen-dokumen ini dilabeli **sebelum eksekusi** dan engine dievaluasi **tanpa mengubah satu baris pun aturan kode** untuk mencocokkannya.

### 1. Ringkasan Hasil Uji Buta Independen (Zero-Tuning)

- **Tanggal Pengujian:** 2026-10-28
- **Skrip Evaluator:** `tests/benchmark_blind.py`
- **Total Dokumen Uji:** 10 Dokumen Independen
- **Verdict Accuracy:** **70.0%** (7 dari 10 dokumen terklasifikasi tepat)
- **Trap Evasion Rate:** **100.0%** (3 dari 3 skenario jebakan lolos tanpa false alarm)
- **Macro Precision:** 17.4%
- **Macro Recall:** 33.3%
- **Macro F1 Score:** 22.8%

### 2. Detail Hasil per Dokumen Uji Buta

| ID Dokumen | Judul Skenario Uji | Expected Verdict | Actual Verdict | Status Evaluasi | Keterangan Kasus |
|---|---|---|---|:---:|---|
| `blind_01` | Rehabilitasi Gedung Kantor (Patuh & Bersih) | `GO` | `GO` | **MATCH** | Memenuhi seluruh syarat administratif & teknis |
| `blind_02` | Laptop Mobilitas (Lock-in Intel Core Ultra) | `NO-GO` | `NO-GO` | **MATCH** | Berhasil mendeteksi penguncian CPU Intel tanpa opsi setara |
| `blind_03` | Kajian Tata Ruang (Jadwal Sangat Mepet) | `NO-GO` | `NO-GO` | **MATCH** | Berhasil menangkap penawaran 4 hari & sanggah 2 hari |
| `blind_04` | CT-Scan RSUD (Denda Keterlambatan Tanpa Batas) | `NO-GO` | `NO-GO` | **MATCH** | Berhasil mendeteksi klausul denda tanpa batas maksimal |
| `blind_05` | Jasa Kebersihan (Pakta Integritas Bebas KKN) | `GO` | `GO` | **MATCH (TRAP)** | Jebakan komitmen integritas normatif lolos tanpa alarm |
| `blind_06` | Jasa ERP (Total BoQ Melebihi Pagu Anggaran) | `NO-GO` | `GO` | **MISMATCH** | **False Negative**: Angka BoQ dalam narasi bebas lolos dari regex tabel |
| `blind_07` | Sewa Kendaraan Dinas (Spesifikasi Merek + Setara) | `GO` | `NO-GO` | **MISMATCH** | **False Positive Verdict**: Klausul merek setara lolos (Trap: PASS), tetapi dokumen minim slot memicu gap administratif |
| `blind_08` | Meubeler Kantor (SBU Kedaluwarsa < 30 Hari) | `BELUM CUKUP BUKTI` | `NO-GO` | **MISMATCH** | Aturan mendeteksi `EXPIRING`, namun kombinasi slot memicu NO-GO |
| `blind_09` | Konsultan Jalan (Billing Rate di Atas INKINDO) | `NO-GO` | `NO-GO` | **MATCH** | Berhasil mendeteksi mark-up tarif tenaga ahli Rp 140 jt/bln |
| `blind_10` | Notulensi Koordinasi (Format Narasi Lepas) | `TIDAK ADA SYARAT TERBACA` | `TIDAK ADA SYARAT TERBACA` | **MATCH (TRAP)** | Berhasil mendeteksi ketiadaan bab syarat teknis |

---

## BAGIAN III: Analisis Kegagalan & Area Kelemahan Engine (Error Analysis)

Evaluasi independen pada blind test set mengungkap kelemahan nyata yang wajib diketahui evaluator:

1. **Keterbatasan Format Narasi Bebas (Kasus `blind_06`)**:
   - *Masalah*: Angka BoQ (Rp 6,25 Miliar) dan Pagu (Rp 5,0 Miliar) yang ditulis dalam paragraf narasi deskriptif tanpa tabel BoQ terstruktur gagal dipicu oleh parser anggaran. Parser saat ini dioptimalkan untuk berkas `.xlsx` dan pola teks bertabel.
   - *Solusi Masa Depan*: Menambahkan modul ekstraksi semantik berbasis LLM (IBM Granite) untuk menangkap entitas anggaran dalam format prosa bebas jika pengguna mengaktifkan mode analisis tambahan.

2. **Interaksi Multi-Slot Dokumen (Kasus `blind_07` & `blind_08`)**:
   - *Masalah*: Mesin aturan bersifat konservatif. Jika dokumen input hanya berisi potongan KAK tanpa melampirkan berkas bukti (NPWP, NIB), mesin menganggap dokumen penawaran belum lengkap sehingga memicu verdict penolakan (NO-GO), meskipun klausul teknisnya sendiri memenuhi syarat.
   - *Solusi Masa Depan*: Memisahkan verdict menjadi dua dimensi: **Verdict KAK/Draf Panitia** (apakah KAK diskriminatif) dan **Verdict Dokumen Penawaran** (apakah berkas penyedia lengkap).

---

## BAGIAN IV: Cara Menjalankan Ulang Benchmark

```powershell
# 1. Jalankan benchmark Development Set (24 dokumen)
python tests/benchmark_heldout.py

# 2. Jalankan benchmark Blind Test Set Independen (10 dokumen)
python tests/benchmark_blind.py
```
