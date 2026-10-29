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

## 3. Kebijakan Penetapan Verdict (Verdict Policy)
Sistem memisahkan secara ketat antara pelanggaran hukum terkonfirmasi vs status administratif yang masih memerlukan klarifikasi:

1. **`NO-GO` (Hanya untuk Cacat Fatal yang Pasti)**:
   - Diberikan **hanya** jika terdapat temuan kesenjangan pasti (`status == "GAP"`):
     * Penguncian merek atau spesifikasi diskriminatif tanpa klausul kesetaraan (Pasal 19 Perpres 12/2021).
     * Jadwal lelang di bawah batas minimum kewajaran LKPP (Pasal 54 Perpres 12/2021).
     * Klausul denda keterlambatan tanpa batas kumulatif (*uncapped poison pill*).
     * Total biaya BoQ melebihi Pagu Anggaran yang tersedia (defisit anggaran).
     * Mark-up tarif man-month konsultan di atas batas pedoman remunerasi nasional.
     * Dokumen legalitas penyedia yang terbukti telah kedaluwarsa sebelum batas akhir penawaran.
     * Terindikasi adanya benturan kepentingan personal/afiliasi yang dilarang.
   - Ketiadaan dokumen penawaran atau masa berlaku yang hampir habis **dilarang keras** memicu status `NO-GO`.

2. **`BELUM CUKUP BUKTI` (Status Terpisah untuk Bukti Kosong & Dokumen Mendekati Kedaluwarsa)**:
   - **Bukti Kosong / Belum Diunggah**: Ketika mengevaluasi draf KAK PPK, slot dokumen penawaran penyedia (NPWP, NIB, SBU, Jaminan) berstatus `REVIEW` karena berkas penyedia memang belum diunggah. Status ini menandakan perlunya kelengkapan berkas, bukan vonis pembatalan paket.
   - **Dokumen Mendekati Kedaluwarsa (`EXPIRING`)**: Dokumen legalitas yang masa berlakunya masih aktif namun kurang dari 30 hari sebelum batas penawaran diberi status `EXPIRING` dengan rekomendasi *BELUM CUKUP BUKTI* agar penyedia menyertakan bukti perpanjangan, bukan vonis diskualifikasi seketika.

3. **`GO`**:
   - Seluruh persyaratan administratif dan teknis yang terbaca telah diverifikasi pemenuhannya dari bukti yang disertakan, dan tidak ada cacat yang pasti.

4. **`TIDAK ADA SYARAT TERBACA`**:
   - Dokumen tidak memuat bab persyaratan kualifikasi, teknis, atau kontrak yang dapat diidentifikasi oleh aturan sistem (misal: berkas pindaian gambar tanpa teks OCR atau notulensi rapat umum).

---

## 4. Batasan Sistem (System Limitations)
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
2. **Validation Set v1 (10 Dokumen — label tidak diubah; engine dikalibrasi setelah putaran pertama dari 70% ke 90%)**:
   - Diuji pertama kali menghasilkan akurasi 70.0% (7/10); pasca-kalibrasi kebijakan konservatif dan parser anggaran naik ke **90.0% (9/10 dokumen)**.
   - **Trap Evasion Rate: 100.0% (3/3 skenario jebakan lolos tanpa false alarm)**.
   - Menunjukkan keandalan tinggi pada klausul lock-in, jadwal mepet, dan denda kontrak, dengan keterbatasan yang diakui pada deteksi angka anggaran dalam format narasi bebas.
   - Laporan perbandingan lengkap tercatat pada `docs/BENCHMARK_RESULTS.md`.

---

## 6. Batasan yang Diketahui (Known Limitations)

1. **Macro Precision, Recall, dan F1 Rendah**:
   - Pada Validation Set v1 (Macro Precision ≈15%, Recall ≈29%, F1 ≈20%) dan Narrative Budget Set (Macro Precision ≈25%, Recall ≈17%, F1 ≈20%), metrik evaluasi per-aturan relatif rendah. Hal ini merupakan konsekuensi langsung dari kebijakan triase konservatif (*Human-in-the-Loop*): sistem sengaja menghindari vonis ekstrem otomatis dan mengalihkan status yang meragukan ke `BELUM CUKUP BUKTI`.
2. **Cakupan Aturan Berbasis Pola Teks (Pattern-Based)**:
   - Logika deteksi mengandalkan ekspresi reguler deklaratif dan pencocokan teks substring; sistem tidak melakukan pemahaman semantik mendalam pada dokumen yang menggunakan metafora atau parafrasa kompleks tanpa model bahasa.
3. **Keterbatasan Bahasa Dokumen**:
   - Sistem dioptimalkan untuk bahasa Indonesia dokumen pengadaan LPSE (istilah KAK, HPS, DIPA, BoQ). Dukungan bahasa Inggris saat ini baru mencakup istilah kunci jadwal ("bidding period", "working days") dan klausul ekuivalensi ("or equivalent").
4. **Deteksi Diskriminasi Regional Spesifik Pola**:
   - Deteksi pembatasan wilayah baru mencakup pola eksplisit domisili ("wajib berdomisili"), asosiasi ("anggota KADIN"), dan kepemilikan kantor cabang lokal yang tidak dikecualikan oleh lokasi pekerjaan sah.
5. **Keamanan Prompt Injection**:
   - Mesin aturan lokal 100% kebal terhadap prompt injection karena beroperasi murni secara deterministik tanpa LLM. Namun, jalur inferensi LLM eksternal opsional (watsonx / Langflow) hanya dilindungi oleh filter sanitasi PII dan verifikasi kutipan teks persis (*exact quote grounding*), bukan pembuktian formal adversarial defense.
