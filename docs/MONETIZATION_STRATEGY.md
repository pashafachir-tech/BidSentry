# Strategi Monetisasi & Go-To-Market (GTM) BidSentry

> **Pembaruan Strategis**: Berdasarkan analisis kelayakan bisnis, BidSentry **tidak bergantung pada siklus pengadaan pemerintah (B2G)** pada Fase 1. Penetrasi pasar difokuskan pada **B2B Enterprise Procurement & Internal Audit** serta **Vendor Bid-Readiness SaaS**.

---

## 1. Analisis Masalah Siklus Penjualan B2G vs Pivot B2B

| Parameter | Jalur Tradisional B2G (Pemerintah/K/L) | Jalur Pivot B2B & Vendor SaaS (BidSentry) |
| :--- | :--- | :--- |
| **Siklus Penjualan** | 12 – 24 Bulan (birokrasi DIPA/APBN) | **2 – 6 Minggu** (tim pengadaan BUMN/swasta & vendor) |
| **Hambatan Regulasi** | Sertifikasi ketat instansi pusat | Integrasi cepat via API/SDK lokal & on-premise |
| **Urgensi Pembeli** | Terikat tahun anggaran | Kebutuhan mendesak: *menghindari gugur lelang & denda kontrak* |
| **Model Pembayaran** | Pembayaran di akhir tahun anggaran | Langganan berulang (ARR) & *usage-based per audit* |

---

## 2. Segmen Pasar Utama (Dual-Track Target Market)

### Jalur 1: Vendor Bid-Readiness SaaS (Self-Audit Pra-Submit)
- **Target Pengguna**: Kontraktor konstruksi swasta, vendor TI, distributor alkes, dan konsultan yang rutin mengikuti tender LPSE/BUMN (estimasi > 200.000 badan usaha aktif di Indonesia).
- **Pain Point**: Gugur administrasi akibat hal sepele (NPWP tidak valid, SBU kedaluwarsa < 30 hari, format jaminan tidak sesuai, salah hitung aritmatika BoQ) atau menandatangani kontrak jebakan (denda keterlambatan tanpa batas).
- **Proposisi Nilai**: Pre-flight audit dalam < 1 menit sebelum unggah ke LPSE, mengeliminasi risiko diskualifikasi teknis/administrasi dan menyusun draf sanggahan resmi secara instan.

### Jalur 2: B2B Enterprise & BUMN Internal Audit (Forensic Compliance)
- **Target Pengguna**: Divisi *Procurement & Supply Chain* BUMN (Pertamina, PLN, Telkom, Waskita, Wijaya Karya, dsb.) serta auditor internal (APIP / Satuan Pengawas Internal).
- **Pain Point**: Audit manual ratusan halaman tender memakan waktu 4–8 jam per paket, rawan lolosnya penguncian spesifikasi (*vendor lock-in*), harga timpang > 110% HPS, dan indikasi kesamaan dokumen antar-penawar.
- **Proposisi Nilai**: Triase instan puluhan vendor secara paralel, deteksi jaringan kesamaan metadata PDF, rekonsiliasi otomatis adendum lelang, dan hash-chained tamper-evident audit trail.

---

## 3. Model Penetapan Harga Berjenjang (Usage-Based & Enterprise License)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: PAY-PER-AUDIT (Starter Vendor)                                                 │
│ Rp 150.000 / paket tender yang diaudit                                                 │
│ • Pindai KAK & dokumen penawaran (PDF/DOCX/XLSX)                                       │
│ • Validasi 15 aturan deterministik Perpres 12/2021                                      │
│ • Ekspor draf surat sanggahan resmi (DOCX)                                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: PROFESSIONAL SAAS (Tim Tender Kontraktor)                                      │
│ Rp 2.500.000 / bulan (hingga 25 tender aktif / tim)                                     │
│ • Seluruh fitur Tier 1 + multi-user collaboration                                      │
│ • Rekonsiliasi adendum multi-versi otomatis                                            │
│ • Ekstraksi entitas semantik berbasis IBM Granite (watsonx.ai)                         │
│ • Kalkulator simulasi skenario denda & over-budget                                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TIER 3: ENTERPRISE ON-PREMISE (BUMN & Korporasi Besar)                                 │
│ Rp 180.000.000 – Rp 350.000.000 / tahun (Lisensi Lembaga Tanpa Batas)                  │
│ • Deployment lokal tertutup (on-premise / private cloud Docker)                        │
│ • Deteksi indikator kesamaan multi-vendor & graf jaringan                              │
│ • Audit trail kriptografis (SHA-256 hash chaining) anti-tampering                      │
│ • Integrasi kustom ke ERP internal (SAP, Oracle) via REST API & Bob MCP               │
│ • SLA respon teknis 24/7 dan pembaruan aturan regulasi tahunan                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Proyeksi Keuangan Unit Ekonomi (Unit Economics)

- **Customer Acquisition Cost (CAC) Vendor**: Estimasi Rp 350.000 via digital marketing B2B dan komunitas asosiasi kontraktor (GAPENSI, INKINDO).
- **Lifetime Value (LTV) Professional**: Estimasi Rp 30.000.000 (retensi rata-rata 12 bulan).
- **Rasio LTV/CAC**: **8.5x** (sangat sehat untuk model B2B SaaS).
- **Gross Margin**: **> 88%** karena mesin aturan inti berjalan secara lokal deterministik dengan konsumsi komputasi token LLM yang minimal (hanya dipanggil atas persetujuan pengguna untuk ekstraksi semantik).

---

## 5. Rencana Pilot & Validasi Lapangan

1. **Fase Pilot Alpha (Bulan 1–2)**: Pengujian gratis terbatas dengan 5 kontraktor menengah dan 2 Satuan Pengawas Internal (SPI) BUMN untuk mengumpulkan metrik waktu audit riil dan efektivitas deteksi red-flag.
2. **Fase Peluncuran Komersial B2B (Bulan 3–6)**: Pembukaan akses langganan SaaS Tier 1 & 2 untuk asosiasi penyedia, diikuti penawaran PoC (Proof of Concept) on-premise untuk korporasi BUMN.
3. **Fase Kemitraan Ekosistem (Bulan 6+)**: Kolaborasi dengan konsultan audit independen dan penyedia solusi pengadaan enterprise sebagai mitra integrasi.
