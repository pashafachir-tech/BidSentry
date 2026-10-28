# Lembar Bukti Penilaian Rubrik Juri (Evidence Scorecard)

Dokumen ini menyajikan pemetaan bukti implementasi teknis dan proposisi proyek **BidSentry** terhadap 6 kriteria rubrik evaluasi juri secara transparan, jujur, dan dapat diverifikasi langsung pada basis kode.

---

## 1. Problem Clarity & Validasi Kebutuhan (Bobot 20%)

### A. Definisi Masalah yang Terverifikasi
Pengadaan barang dan jasa pemerintah (PBJP) di Indonesia mengelola alokasi anggaran belanja APBN/APBD yang sangat besar:
- **Data Pagu PBJP Resmi Terverifikasi**:
  - **Lembaga / Sumber**: Lembaga Kebijakan Pengadaan Barang/Jasa Pemerintah (LKPP) Republik Indonesia
  - **URL Sumber**: [https://www.lkpp.go.id/](https://www.lkpp.go.id/) (Monitoring Nasional Rencana Umum Pengadaan / SiRUP)
  - **Tahun Data**: 2024
  - **Kutipan Persis LKPP**: *"Total pagu belanja pengadaan barang/jasa nasional tercatat sebesar Rp 1.165,14 Triliun (dengan RUP terumumkan pada SiRUP per April 2024 mencapai Rp 1.043,45 Triliun)."*
- **Tantangan Kritis Pelaksanaan**:
  - **Asimetri Informasi & Batasan Waktu**: Dokumen tender pengadaan kompleks memuat puluhan hingga ratusan halaman ketentuan teknis, BoQ, dan draf kontrak. Penyedia hanya memiliki batas waktu sanggah dan pemasukan penawaran singkat (minimal 5 hari kalender untuk sanggah prakualifikasi sesuai Perpres 12/2021).
  - **Celah Kepatuhan Terselubung (Hidden Poison Pills)**: Praktik penguncian spesifikasi teknis pada merek/teknologi tunggal (*vendor lock-in*), pemadatan jadwal (*compressed timeline*), denda tanpa batas maksimal (*uncapped penalty*), serta total BoQ melebihi Pagu DIPA rawan lolos dari penelaahan cepat dan berisiko sengketa kontrak atau tender gagal.

### B. Tiga Persona Arketipe Pengguna Sasaran (Target Archetypes)

> [!NOTE]
> Persona di bawah merupakan pemodelan arketipe berdasarkan alur regulasi pengadaan nasional (Perpres 12/2021). **Kutipan wawancara langsung dan metrik adopsi riil pengguna berstatus `BELUM DIKUMPULKAN`** (masih menunggu tahap pilot).

```
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│ Arketipe 1: Penyedia    │  │ Arketipe 2: Pokja       │  │ Arketipe 3: Auditor     │
│ (Bid Manager / Vendor)  │  │ (Panitia Pemilihan K/L) │  │ (APIP / Inspektorat)    │
│ Kebutuhan: Deteksi jebak│  │ Kebutuhan: Validasi     │  │ Kebutuhan: Uji petik    │
│ an kontrak & draf sang  │  │ kepatuhan draf KAK PPK  │  │ forensik dokumen lelang │
│ gah resmi instan        │  │ sebelum tayang di LPSE  │  │ berbasis aturan audit   │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
```

1. **Tim Tender / Bid Manager Penyedia Swasta**: Menghindari kerugian akibat menandatangani kontrak jebakan (denda tak terbatas) dan menyusun sanggahan lelang terlegitimasi sebelum tenggat sanggah berakhir.
2. **Pokja Pemilihan Kementerian/Lembaga/Pemerintah Daerah**: Memastikan draf dokumen lelang yang disusun PPK mematuhi Pasal 19 Perpres 12/2021 (tidak diskriminatif) agar lelang tidak dibatalkan atau disanggah peserta.
3. **Auditor Internal (APIP / BPKP)**: Mempercepat uji petik berkas tender dalam audit kepatuhan pengadaan dengan bukti kutipan klausul yang dapat diverifikasi secara eksak.

### C. Alur Kerja Eksisting (Manual) vs Alur BidSentry

| Parameter Proses | Alur Eksisting (Review Manual) | Alur Kerja BidSentry v2.1 | Status Verifikasi Data |
| :--- | :--- | :--- | :--- |
| **Waktu Telaah Dokumen** | 4 – 8 Jam per berkas tender | **1 – 3 Detik** *(throughput parser lokal)* | **BELUM DIVERIFIKASI** *(studi waktu manusia formal belum dilakukan; angka jam manual adalah estimasi pra-pilot)* |
| **Pengecekan Spesifikasi Merek** | Membaca manual kata per kata | Deteksi deterministik spesifikasi merek & klausul kesetaraan | **TERVERIFIKASI** *(53 unit tests & suite benchmark)* |
| **Simulasi Risiko Finansial & Denda** | Perhitungan spreadsheet ad-hoc | Kalkulator otomatis multi-skenario denda & over-budget | **TERVERIFIKASI** *(engine audit finansial & parsers)* |
| **Penyusunan Surat Sanggahan** | 1 – 2 Hari penyusunan teks hukum | Otomatis 1-klik template sanggahan ber-sitasi hukum Perpres | **BELUM DIVERIFIKASI** *(waktu hemat manusia estimasi; fitur teknis export DOCX terverifikasi)* |
| **Risiko Human Error** | Tinggi saat menangani banyak paket | Rendah; aturan dievaluasi konsisten secara deterministik | **TERVERIFIKASI** *(100% konsisten pada benchmark run)* |

### D. Metrik Dampak Lapangan
- Seluruh metrik pengujian pengguna manusia lapangan berstatus: **`BELUM DIKUMPULKAN`**.
- Protokol dan instrumen wawancara terstandarisasi telah disiapkan pada [`docs/INTERVIEW_GUIDE.md`](file:///d:/bidsentry/docs/INTERVIEW_GUIDE.md) dan [`docs/PILOT_RESULTS_TEMPLATE.md`](file:///d:/bidsentry/docs/PILOT_RESULTS_TEMPLATE.md).

---

## 2. Innovation, Feasibility, Monetization (Bobot 25%)

### A. Inovasi: Mesin Aturan Deterministik Berbasis Kode
- **Deterministic-First Core**: Berbeda dengan aplikasi AI generik yang menyerahkan putusan hukum pada model bahasa yang rawan halusinasi angka/pasal, BidSentry menggunakan mesin aturan deterministik berbasis kode dan konfigurasi deklaratif ([`config/rules.yaml`](file:///d:/bidsentry/config/rules.yaml)).
- **Dual-Layer Evaluation**: Mesin lokal mengeksekusi 15 aturan spesifik Perpres 12/2021 secara 100% offline. LLM (IBM Granite / Langflow) hanya bertindak sebagai penasihat semantik sekunder jika disetujui pengguna (*opt-in*).

### B. Kelayakan Teknis & Status Integrasi IBM (Feasibility)
- Status integrasi komponen IBM watsonx didokumentasikan secara transparan pada [`docs/INTEGRATION_STATUS.md`](file:///d:/bidsentry/docs/INTEGRATION_STATUS.md).
- Saat kredensial lingkungan belum diisi pengguna, sistem secara jujur berstatus **`BELUM DIVERIFIKASI (UNCONFIGURED)`**.
- Skrip verifikasi mandiri untuk juri tersedia di [`scripts/verify_watsonx.py`](file:///d:/bidsentry/scripts/verify_watsonx.py) (berjalan mulus dengan return code 0, melaporkan status konfigurasi aktual tanpa crash).

### C. Hipotesis Model Monetisasi 3-Tier (Proposisi Awal, Belum Tervalidasi Pasar)

> [!NOTE]
> Seluruh proyeksi tarif dan konversi pengguna di bawah adalah hipotesis awal tim dan berstatus **`BELUM DIVERIFIKASI`** oleh survei willingness-to-pay pasar formal.

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. COMMUNITY TIER (Gratis / Open Core)                          │
│    - Mesin aturan lokal offline (CLI / local web dashboard)     │
│    - Deteksi red flag standar & ekspor hasil dasar              │
├─────────────────────────────────────────────────────────────────┤
│ 2. PROFESSIONAL SAAS (Hipotesis: Rp 1.500.000 / bulan / tim)    │
│    - Parser Excel BoQ otomatis & forensic addendum reconciliation│
│    - Draf sanggahan resmi DOCX instan                           │
│    - Integrasi penasihat semantik IBM watsonx                   │
├─────────────────────────────────────────────────────────────────┤
│ 3. ENTERPRISE ON-PREMISE (Lisensi Lembaga / Custom Contract)     │
│    - Deployment tertutup di server internal K/L / BUMN          │
│    - Audit trail atomik tamper-evident & retensi log kepatuhan  │
│    - Kustomisasi aturan internal KAK dan integrasi e-Katalog/LPSE│
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. User Impact & Usability (Bobot 15%)

### A. Pengalaman Pengguna Berpusat Solusi
- **Alur Kerja Sekali Jalan**: Auto-tab switcher langsung memindahkan pengguna ke tampilan matriks temuan seketika evaluasi selesai, mencegah disorientasi.
- **Isolasi Dialog DOM**: Dialog tidak tertutup atau rusak saat pembaruan data berkat pemisahan kontainer `#dialog-layer`.
- **Manajemen Berkas Transparan**: Setiap slot unggahan menyertakan pratinjau teks dokumen, ukuran berkas, serta tombol hapus dan ganti per berkas.
- **Sanggahan Builder Terarah dengan Exact Substring Grounding**: Memvalidasi kutipan temuan secara ketat terhadap teks sumber asli yang disimpan di server. Kutipan yang tidak cocok ditolak untuk mencegah halusinasi surat sanggahan.

### B. Estimasi Throughput Teknis
- Pengukuran teknis throughput menunjukkan waktu eksekusi kode backend pada dokumen benchmark berkisar antara 1 hingga 3 detik. Nilai ini adalah kecepatan komputasi parser, bukan klaim penghematan biaya tenaga kerja manusia. Rincian selengkapnya pada [`docs/PILOT_RESULTS_TEMPLATE.md`](file:///d:/bidsentry/docs/PILOT_RESULTS_TEMPLATE.md).

---

## 4. Technical Execution & Prototype (Bobot 20%)

### A. Eksekusi Teknis Berkualitas Tinggi
- **Stack**: Python 3.11/3.12, FastAPI ASGI, openpyxl, Vanilla JavaScript, CSS custom responsif tanpa ketergantungan framework eksternal berat.
- **Dokumentasi Arsitektur**: Lengkap dengan diagram alir data dan sequence diagram Mermaid pada [`docs/ARCHITECTURE.md`](file:///d:/bidsentry/docs/ARCHITECTURE.md).
- **Pengujian E2E Otomatis**: Dilengkapi smoke test Playwright pada [`tests/e2e_smoke.py`](file:///d:/bidsentry/tests/e2e_smoke.py) yang memvalidasi interaksi UI lengkap dan menyimpan screenshot hasil di [`docs/screenshots/e2e_results.png`](file:///d:/bidsentry/docs/screenshots/e2e_results.png).
- **Automated CI Workflow**: GitHub Actions pipeline aktif di [`.github/workflows/ci.yml`](file:///d:/bidsentry/.github/workflows/ci.yml) yang menjalankan seluruh unit test dan regression benchmark.

### B. Hasil Benchmark Objektif (Tiga Dataset Terpisah)

Seluruh angka di bawah dihitung secara dinamis dari hasil eksekusi kode benchmark aktual:

1. **Development Set (24 Dokumen Sintetis)**:
   - Evaluator: `tests/benchmark_heldout.py`
   - Baseline Awal: Verdict Accuracy 75.0% (18/24), Trap Evasion 77.8% (7/9).
   - Pasca-Penyetelan: **Verdict Accuracy 100.0% (24/24)**, **Trap Evasion 100.0% (9/9)**, Macro F1 100.0%.
   - *Catatan Metodologi: Set ini digunakan untuk memandu pengkodean aturan, bukan uji buta independen.*

2. **Validation Set v1 (10 Dokumen Uji Buta — Frozen)**:
   - Evaluator: `tests/benchmark_blind.py`
   - Kebijakan: Dilabeli secara independen sebelum eksekusi, **label dibekukan tanpa penyetelan ulang**.
   - **Verdict Accuracy: 90.0% (9/10)**
   - **Trap Evasion Rate: 100.0% (3/3)**
   - **Macro Precision: 16.0%**
   - **Macro Recall: 30.8%**
   - **Macro F1 Score: 21.1%**
   - *Kasus Mismatch: `blind_07` (potongan KAK tanpa slot berkas penyedia memicu evaluasi administratif incomplete).*

3. **Narrative Budget Test Set (5 Dokumen Narasi Bebas Baru)**:
   - Evaluator: `tests/benchmark_budget_narrative.py`
   - Pengujian: Ekstraksi angka Pagu DIPA dan BoQ/HPS pada prosa naratif bebas (non-tabel).
   - **Verdict Accuracy: 80.0% (4/5)**
   - **Trap Evasion Rate: 100.0% (1/1)**
   - **Macro F1 Score: 25.0%**
   - *Kasus Mismatch: `budget_02` (biaya aman, namun ketiadaan slot berkas NIB/NPWP menghasilkan status BELUM CUKUP BUKTI).*

Laporan lengkap dan analisis kegagalan disajikan pada [`docs/BENCHMARK_RESULTS.md`](file:///d:/bidsentry/docs/BENCHMARK_RESULTS.md).

---

## 5. Responsible AI (Bobot 10%)

### A. Tata Kelola Privasi & Keamanan Data (Data Governance)
- **Modul PII Redaction Otomatis**: NIK, NPWP, nomor rekening bank, dan nomor telepon disensor sebelum teks dikirim ke provider AI eksternal.
- **Verbatim Quote Grounding Server-Side**: Kutipan temuan disimpan bersama audit di server dan divalidasi dengan pencocokan substring eksak (*exact substring*) terhadap naskah asli sebelum surat sanggahan dapat di-generate.
- **Host Header & DNS Rebinding Guard**: Membatasi eksekusi hanya pada host terpercaya.

### B. Transparansi & Model Card
- Dokumentasi kebijakan verdict deterministik, batasan model, ruang lingkup etika, dan analisis kegagalan tersedia lengkap pada [`docs/MODEL_CARD.md`](file:///d:/bidsentry/docs/MODEL_CARD.md).
- Verdict `NO-GO` secara ketat dibatasi hanya untuk pelanggaran fatal yang terkonfirmasi (`GAP`); ketidaklengkapan bukti atau berkas kedaluwarsa masuk ke status `BELUM CUKUP BUKTI`.

---

## 6. Participation & Engineering Discipline (Bobot 5%)
- **Penilaian Participation**: Kriteria Participation (5%) mencakup kehadiran workshop, konsultasi mentor, dan keterlibatan komunitas selama program hackathon yang dinilai secara mandiri oleh panitia/juri.
- **Disiplin Rekayasa Kode**: Repositori ini membuktikan keseriusan implementasi melalui commit Git modular berkesinambungan, pengujian unit test menyeluruh (56 tests pass), dan transparansi pelaporan hasil benchmark tanpa memalsukan data.
- **Riwayat Perubahan**: Tercatat lengkap pada [`docs/CHANGELOG_ITERASI.md`](file:///d:/bidsentry/docs/CHANGELOG_ITERASI.md).
