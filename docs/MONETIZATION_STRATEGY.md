# Strategi Monetisasi & Model Bisnis Micro-SaaS BidSentry

> **Pendekatan Strategis**: BidSentry mengadopsi model **Lean Micro-Utility & Micro-SaaS** yang membumi dan dapat dieksekusi langsung. Sistem tidak bergantung pada siklus pengadaan pemerintah yang panjang (B2G 12–24 bulan), melainkan menyasar transaksi mikro langsung dari kontraktor peserta lelang (CV/UMKM) serta belanja operasional rutin unit pengadaan daerah (BUMD/BLUD) melalui skema Pengadaan Langsung non-tender.

---

## 1. Struktur Harga & Unit Economics Riil

Model penetapan harga dirancang tanpa friksi birokrasi (*frictionless adoption*), memadukan pembayaran eceran berbasis QRIS instan dan langganan bulanan terjangkau:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: PAY-PER-AUDIT (QRIS Instant Voucher)                                          │
│ Rp 5.000 untuk 10 kali audit (efektif Rp 500 / dokumen)                               │
│ • Pembelian kuota instan via QRIS (mengatasi batas minimum aggregator payment gateway) │
│ • Validasi kepatuhan 14 aturan deterministik Perpres 12/2021                           │
│ • Pengecekan cepat H-1 sebelum submit dokumen penawaran ke SPSE/LPSE                   │
│ • Hasil audit instan (< 30 detik) dengan ringkasan status kelayakan                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: VENDOR PRO SUBSCRIPTION (Langganan Bulanan Kontraktor)                         │
│ Rp 300.000 / bulan (setara Rp 10.000 / hari)                                           │
│ • Kuota audit reguler hingga 30 paket tender / bulan tanpa biaya tambahan              │
│ • Pre-flight checklist kelayakan berkas administratif (NIB, SBU, KSWP, NPWP)          │
│ • Deteksi klausul diskriminatif KAK (brand lock-in, jadwal mepet, denda tanpa batas)   │
│ • Generator otomatis draf Surat Sanggahan resmi format .docx berbasis Perpres 12/2021  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: BUMD / BLUD / UNIT PENGADAAN PILOT (Langganan Bulanan Instansi Lokal)          │
│ Rp 800.000 / bulan (setara Rp 9,6 Juta / tahun — di bawah pagu Pengadaan Langsung)     │
│ • Kuota audit multi-vendor hingga 100 dokumen / bulan tanpa biaya tambahan             │
│ • Audit komparatif rincian BoQ Excel (.xlsx) vs pagu HPS & deteksi over-budget        │
│ • Deteksi indikasi kolusi & kesamaan metadata penawar (Pasal 22 UU No. 5/1999)         │
│ • Akses kolaborasi multi-user auditor (hingga 3 akun pemeriksa)                        │
│ • Generator otomatis Berita Acara Hasil Pemilihan (BAHP) format .docx                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Rincian Biaya Operasional (COGS) & Margin Komputasi

| Komponen | Tier 1: Pay-Per-Audit | Tier 2: Vendor Pro | Tier 3: BUMD / BLUD Pilot |
| :--- | :--- | :--- | :--- |
| **Harga Jual Rata-Rata** | Rp 500 / audit (Rp 5.000 / paket) | Rp 300.000 / bulan (~Rp 10.000 / audit) | Rp 800.000 / bulan (~Rp 8.000 / audit) |
| **Beban Komputasi Lokal (Python)** | Rp 0 (Deterministik CPU lokal) | Rp 0 (Deterministik CPU lokal) | Rp 0 (Deterministik CPU lokal) |
| **Token Inferensi IBM Granite** | ~Rp 200 – Rp 350 per audit | ~Rp 200 – Rp 350 per ringkasan | ~Rp 200 – Rp 350 per telaah |
| **Biaya Transaksi QRIS (MDR 0,7%)** | Rp 35 per voucher Rp 5.000 | Rp 2.100 per transfer bulanan | Rp 5.600 per transfer SPK |
| **Gross Margin Komputasi** | **> 85.0%** | **> 90.0%** | **> 92.0%** |

> **Catatan Efisiensi Arsitektur**: Karena 90% proses analisis (aritmetika BoQ, verifikasi batas denda, pencocokan jadwal, dan pengecekan aturan hukum) dieksekusi secara deterministik pada mesin lokal Python tanpa memanggil API pihak ketiga, konsumsi token LLM IBM Granite 3-8B Instruct via watsonx.ai hanya digunakan saat pengguna meminta ringkasan naratif eksekutif. Hal ini mempertahankan *gross margin* di atas 85% secara stabil.

---

## 2. Realistic Bottom-Up Market Sizing

Perhitungan potensi pasar didasarkan pada data faktual transaksi Sistem Pengadaan Secara Elektronik (SPSE) Lembaga Kebijakan Pengadaan Barang/Jasa Pemerintah (LKPP):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TOTAL ADDRESSABLE MARKET (TAM): Rp 18,5 Miliar / Tahun                                 │
│ 1,25 Juta dokumen penawaran tender per tahun di seluruh sistem LPSE nasional           │
│ (250.000 paket pengadaan lelang × rata-rata 5 penawar per paket tender)                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ SERVICEABLE ADDRESSABLE MARKET (SAM): Rp 2,2 Miliar / Tahun                            │
│ Ekosistem pengadaan regional Jawa Timur: ~150.000 dokumen penawaran tender per tahun   │
│ dan ~350 kontraktor / penyedia aktif skala kecil-menengah yang rutin mengikuti tender  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ SERVICEABLE OBTAINABLE MARKET (SOM — Target Tahun 1): Rp 139,6 Juta / Tahun            │
│ Target akuisisi tahun pertama pada ekosistem kontraktor & unit pengadaan Jawa Timur    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Rincian Komposisi Akuisisi Pendapatan Tahun 1 (SOM: Rp 139,6 Juta):

1. **Audit Eceran UMKM (Voucher QRIS)**:
   - Volume: 18.000 dokumen audit eceran (dikonversi dari ~2.480 transaksi voucher paket Rp 5.000/10 kredit).
   - Proyeksi Pendapatan: **Rp 12.400.000 / tahun**.
   - Karakteristik: Kontraktor mikro yang hanya membutuhkan pengecekan mendesak saat H-1 batas unggah penawaran lelang.

2. **Kontraktor Langganan Aktif (Vendor Pro)**:
   - Volume: 30 vendor kontraktor aktif langganan bulanan (Rp 300.000 / bulan).
   - Proyeksi Pendapatan: 30 vendor × Rp 300.000 × 12 bulan = **Rp 108.000.000 / tahun**.
   - Karakteristik: Kontraktor kelas menengah yang rutin mengikuti 2–4 lelang setiap bulan dan memanfaatkan fitur generator draf Surat Sanggahan resmi.

3. **Instansi BUMD / BLUD Percontohan (Pilot Regional)**:
   - Volume: 2 instansi pengadaan percontohan (misalnya RSUD BLUD daerah atau BUMD Air Minum/Pasar) dengan paket Rp 800.000 / bulan.
   - Nilai Kontrak: Rp 9,6 Juta / instansi / tahun (berada jauh di bawah pagu Pengadaan Langsung Rp 50 Juta / Rp 200 Juta, sehingga cukup diterbitkan Surat Perintah Kerja / SPK langsung tanpa proses tender).
   - Proyeksi Pendapatan: 2 instansi × Rp 800.000 × 12 bulan = **Rp 19.200.000 / tahun**.

**Total Target Pendapatan Tahun 1**: **Rp 139.600.000** dengan estimasi beban token IBM watsonx.ai < Rp 18 Juta (Gross Margin bersih > 87%).

---

## 3. Analisis Lanskap Kompetitor (Competitive Landscape Matrix)

BidSentry diposisikan secara strategis untuk mengisi celah kritis yang tidak dilayani oleh sistem eksisting maupun produk AI generik:

| Kriteria Evaluasi | 1. SPSE / LPSE LKPP (Status Quo) | 2. Platform Intelijen Tender (TenderPlus, dsb.) | 3. Enterprise Contract AI (Luminance, Kira Systems) | 4. Generic LLM Chatbot (ChatGPT, Claude) | 5. BidSentry (Micro-SaaS) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fokus Utama** | Repositori transaksi unggah dokumen lelang | Notifikasi & agregasi peluang lelang baru | Review kontrak hukum korporasi multinasional | Asisten percakapan teks umum | **Audit kepatuhan teknis, BoQ, dan draf sanggahan** |
| **Audit Isi KAK & Syarat Teknis** | Tidak ada (manual oleh panitia) | Tidak ada (hanya scraping judul & pagu) | Terbatas pada klausul umum non-LKPP | Rawan halusinasi pasal & salah hitung | **Otomatis & Terverifikasi (14 Aturan Perpres 12/2021)** |
| **Pembedahan Tabel BoQ (.xlsx)** | Tidak ada | Tidak ada | Jarang / Add-on enterprise mahal | Gagal membaca multi-sheet / rumus dinamis | **Bawaan (Native openpyxl) dengan simulasi defisit** |
| **Konteks Hukum Pengadaan Indonesia** | Ya (sebagai sistem induk) | Hanya metadata pengumuman | Tidak (berorientasi US/UK Common Law) | Rendah (mencampur aturan lama/baru) | **Spesifik Perpres 16/2018 jo. 12/2021 & UU 5/1999** |
| **Deteksi Jebakan Merek & Batas Denda** | Tergantung ketelitian Pokja | Tidak tersedia | Kaku (flagging semua nama merk) | Inkonsisten | **Cerdas (Mengecualikan frasa setara & denda capped)** |
| **Pelindungan Data Pribadi (UU PDP)** | Standar pemerintah | Mengambil data publik | Server luar negeri (non-kedaulatan data) | **Tinggi risiko bocor ke server publik** | **Lokal-First: PII Scrubber sebelum inferensi AI** |
| **Struktur Biaya** | Gratis (Fasilitas Negara) | Langganan Rp 1 Jt – 5 Jt / tahun | Lisensi ratusan juta rupiah per tahun | USD $20 / bulan (~Rp 320.000) | **Mikro: Mulai Rp 500 / audit (Voucher Rp 5.000 QRIS)** |

### Parit Pertahanan & Keunggulan Kompetitif (Moat):

1. **Arsitektur Hibrida Neuro-Symbolic**: Putusan audit hukum (*verdict* GO / NO-GO) dan validasi aritmetika BoQ dijamin 100% deterministik oleh kode Python lokal bebas halusinasi, sementara IBM watsonx.ai Granite 3-8B Instruct bertugas mensintesis temuan kompleks ke dalam bahasa manusia yang persuasif.
2. **Kepatuhan Kedaulatan Data (UU PDP No. 27/2022)**: Seluruh metadata identitas, NIK, NPWP, dan nomor rekening disanitasi secara lokal sebelum dikirimkan ke model AI, melindungi kerahasiaan dokumen penawaran vendor.
3. **Harga Mikro Tanpa Hambatan Birokrasi**: Menawarkan voucher QRIS instan Rp 500/dokumen yang dapat langsung dibeli dari ponsel cerdas penawar lelang tanpa kontrak korporasi berbelit.

---

## 4. Rencana Validasi Lapangan & Go-To-Market (GTM)

1. **Bulan 1–3 (Penyebaran Grassroots & Komunitas Konstruksi)**:
   - Pendekatan langsung ke asosiasi kontraktor daerah di Jawa Timur (GAPENSI, GAPEKSI, INKINDO).
   - Demonstrasi langsung "Pre-flight audit lelang dalam 30 detik: Menghindari diskualifikasi akibat SBU/klausul diskriminatif".
   - Distribusi 500 voucher QRIS gratis untuk memicu adopsi awal dan pengumpulan testimoni.
2. **Bulan 4–6 (Konversi Vendor Pro & Pilot BUMD)**:
   - Konversi 30 kontraktor aktif yang rutin mengikuti lelang ke paket langganan Vendor Pro (Rp 300.000/bulan).
   - Inisiasi percontohan Pengadaan Langsung (SPK Rp 800.000/bln) dengan 2 unit pengadaan RSUD / BUMD lokal untuk pembuktian audit multi-vendor dan pencegahan persekongkolan tender.
3. **Bulan 7–12 (Ekspansi Regional & Skalabilitas SaaS)**:
   - Ekspansi ke wilayah Jawa Tengah dan D.I. Yogyakarta melalui kemitraan dengan konsultan pendamping tender independen.
