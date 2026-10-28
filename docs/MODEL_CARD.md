# BidSentry Model & Decision System Card

## 1. Ikhtisar Sistem & Arsitektur Keputusan
BidSentry adalah sistem hibrida untuk audit kepatuhan dokumen pengadaan publik Indonesia. Sistem memisahkan secara tegas dua lapisan evaluasi:

```
[ Dokumen Pengadaan (KAK / Dokumen Pemilihan) ]
                       │
                       ▼
         [ Ekstraksi Teks & Normalisasi ]
                       │
                       ▼
    ┌────────────────────────────────────────┐
    │ LAPISAN 1: Mesin Deterministik Lokal   │
    │ (config/rules.yaml + engine.py)        │ ──► Menghasilkan Temuan Hukum,
    │ - Pola RegEx & Validasi Logika Ketat   │     Status Kepatuhan, Skor Risiko,
    │ - 100% Berjalan Lokal & Offline        │     dan Rekomendasi Verdict (GO/NO-GO)
    └────────────────────────────────────────┘
                       │ (Hanya bila persetujuan pengguna aktif)
                       ▼
    ┌────────────────────────────────────────┐
    │ LAPISAN 2: Penasihat Semantik (LLM)    │
    │ (IBM watsonx Granite / Langflow)       │ ──► Menyarankan Konteks Sekunder
    │ - Didahului Redaksi Data Pribadi (PII) │     (Ringkasan Kualifikasi, SLA)
    │ - Rekonstruksi Kutipan Asli (Recovery) │     TIDAK mengubah verdict hukum
    └────────────────────────────────────────┘
```

### Batasan Tegas (System Boundaries):
1. **Aturan Deterministik Mengikat**: Keputusan hukum (seperti diskriminasi spesifikasi merek, jadwal di bawah batas minimum LKPP, klausul denda tanpa batas, atau defisit anggaran BoQ vs Pagu) dievaluasi **hanya** oleh mesin aturan berbasis Perpres 12/2021 dan peraturan turunannya. Model bahasa (LLM) dilarang mengubah status hukum atau verdict secara sepihak.
2. **Karakter LLM Bersifat Penasihat (Advisory)**: LLM bertindak sebagai asisten pencari konteks sekunder. Setiap kutipan yang dihasilkan LLM wajib diverifikasi sebagai *exact substring* dari dokumen sumber sebelum ditampilkan kepada pengguna.

---

## 2. Kebijakan Privasi & Redaksi Data Pribadi (PII Redaction)
Untuk melindungi kerahasiaan dokumen penawaran dan data pribadi sebelum transmisi ke provider model eksternal (watsonx / Langflow):

### Entitas yang Dimasking Secara Otomatis:
- **NIK (Nomor Induk Kependudukan)**: Format 16 digit angka Indonesia disensor menjadi `[NIK-REDACTED]`.
- **NPWP (Nomor Pokok Wajib Pajak)**: Format 15/16 digit disensor menjadi `[NPWP-REDACTED]`.
- **Nomor Telepon**: Nomor telepon genggam (awalan `+62` atau `08`) disensor menjadi `[PHONE-REDACTED]`.
- **Alamat Surel (Email)**: Format email disensor menjadi `[EMAIL-REDACTED]`.
- **Nomor Rekening Bank**: Format nomor rekening perbankan disensor menjadi `[REKENING-REDACTED]`.

### Pemulihan Kutipan Asli (Verbatim Quote Recovery):
Jika LLM mengembalikan kutipan yang mengandung placeholder redaksi (misal `[NIK-REDACTED]`), modul `bidsentry.lib.pii.recover_unmasked_quote` memetakan kembali placeholder ke potongan teks asli dokumen sumber pengguna secara aman di lingkungan lokal, sehingga audit trail tetap memiliki bukti tekstual utuh tanpa membocorkan data pribadi ke penyedia cloud AI.

---

## 3. Batasan Sistem (System Limitations)
1. **Bukan Nasihat Hukum (Not Legal Advice)**: BidSentry adalah alat bantu telaah administratif dan teknis. Hasil evaluasi tidak memiliki kekuatan hukum pembatalan lelang dan tidak menggantikan wewenang Pokja Pemilihan atau Pengadilan Tata Usaha Negara.
2. **Indeks Triase Risiko Bukan Vonis Fraud**: Skor risiko (0–100) dan klasifikasi (LOW / MEDIUM / HIGH / CRITICAL) merupakan indeks triase untuk membantu auditor atau penyedia memprioritaskan telaah dokumen, bukan penetapan adanya tindak pidana korupsi.
3. **Ketergantungan Ekstraksi Teks**: Sistem bergantung pada keterbacaan teks digital. PDF hasil pindai (scan) tanpa lapisan OCR tidak dapat dianalisis secara akurat dan akan menampilkan status `TIDAK ADA SYARAT TERBACA`.

---

## 4. Analisis Potensi Kesalahan (Error & Failure Analysis)

| Karakteristik Dokumen | Potensi Masalah | Mitigasi BidSentry |
| :--- | :--- | :--- |
| **Pindaian Citra Murni (Scanned PDF)** | Teks tidak dapat diekstrak oleh parser PDF standar. | Sistem mendeteksi panjang teks nol dan memberikan notifikasi ramah pengguna untuk melakukan OCR terlebih dahulu. |
| **Tabel BoQ / Anggaran Kompleks** | Format multi-kolom dan sel terdistorsi dalam konversi PDF teks. | Didukung modul parser berkas Excel asli (`.xlsx`) via `openpyxl` yang membaca angka numerik dan struktur kolom secara presisi. |
| **Klausul Terpecah Lintas Baris** | Pemotongan kalimat oleh *line-break* pada PDF dua kolom. | Modul normalisasi merekonstruksi paragraf lintas baris (`_lines()` paragraph stitching) sambil tetap mempertahankan indeks baris asal. |
| **Penyebutan Merek yang Diperbolehkan** | Dokumen menyebutkan merek namun diikuti klausul kesetaraan ("atau setara"). | Pengecualian klausul kesetaraan otomatis mengenali frasa "atau setara", "setara", atau "equivalent", mencegah *false positive* pada aturan lock-in. |

---

## 5. Metrik Evaluasi & Pemantauan (Benchmark Evaluasi)
Sistem diuji dengan dua dataset terpisah:
1. **Dataset Pengembangan & Penyetelan (Development Set — 24 Dokumen Sintetis)**:
   - Digunakan untuk memandu kalibrasi aturan deterministik.
   - Baseline awal: Akurasi Verdict 75.0%, Trap Evasion 77.8% (7/9).
   - Pasca-Penyetelan: Akurasi Verdict 100.0% (24/24), Trap Evasion 100.0% (9/9).
2. **Dataset Uji Buta Independen (Blind Test Set — 10 Dokumen Tanpa Penyetelan Aturan)**:
   - Dijalankan secara *zero-tuning* untuk mengukur generalisasi nyata.
   - **Akurasi Verdict: 70.0% (7/10 dokumen)**.
   - **Trap Evasion Rate: 100.0% (3/3 skenario jebakan lolos tanpa false alarm)**.
   - Menunjukkan keandalan tinggi pada klausul lock-in, jadwal mepet, dan denda kontrak, dengan keterbatasan yang diakui pada deteksi angka anggaran dalam format narasi bebas.
   - Laporan perbandingan lengkap tercatat pada `docs/BENCHMARK_RESULTS.md`.
