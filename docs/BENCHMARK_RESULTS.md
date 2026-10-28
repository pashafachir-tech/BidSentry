# Hasil Benchmark Independen BidSentry (Held-out Dataset)

## Baseline Sebelum Perbaikan (Initial Baseline)

- **Tanggal:** 2026-10-28 (2026-10-28T04:10:49.632704+00:00)
- **Commit Hash:** `f094ef8`
- **Jumlah Dokumen Uji:** 24 dokumen sintetis held-out (termasuk 8 kasus jebakan/negatif)
- **Verdict Accuracy:** 75.0% (18/24)
- **Trap Evasion Rate:** 77.8% (tingkat ketepatan menghindari false flag pada klausul jebakan)
- **Macro Precision:** 82.1%
- **Macro Recall:** 89.3%
- **Macro F1 Score:** 85.6%

### Tabel Akurasi Per Aturan / Temuan

| Aturan (Rule ID) | Dokumen Relevan | TP | FP | FN | Precision | Recall | F1 Score | Keterangan Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ADM-KSWP` | 2 | 2 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `ADM-NIB` | 1 | 0 | 1 | 1 | 0.0% | 0.0% | 0.0% | **Perlu Perbaikan (Precision < 80%)** |
| `ADM-NPWP` | 3 | 3 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `ADM-SBU` | 2 | 1 | 1 | 1 | 50.0% | 50.0% | 50.0% | **Perlu Perbaikan (Precision < 80%)** |
| `ADM-WARRANTY` | 2 | 2 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `CON-PENALTY` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `FIN-DOUBLE-LICENSE` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `FIN-MARKUP-RATE` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `FIN-OVER-BUDGET` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `GOV-CONFLICT-INTEREST` | 2 | 1 | 1 | 0 | 50.0% | 100.0% | 66.7% | **Perlu Perbaikan (Precision < 80%)** |
| `PROC-TIMELINE-COMPRESSED` | 2 | 2 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `SPEC-LOCKIN-CPU` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |
| `SPEC-LOCKIN-GPU` | 2 | 1 | 1 | 0 | 50.0% | 100.0% | 66.7% | **Perlu Perbaikan (Precision < 80%)** |
| `SPEC-REGIONAL-LOCKIN` | 1 | 1 | 0 | 0 | 100.0% | 100.0% | 100.0% | Aman (Precision ≥ 80%) |

