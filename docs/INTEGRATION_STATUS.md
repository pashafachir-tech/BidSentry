# Status Integrasi Teknologi IBM & Layanan Eksternal

> **Dokumen Transparansi Teknis**: Dihasilkan oleh `scripts/verify_watsonx.py`.
> Terakhir diperbarui: 2026-10-29 11:38:33 UTC

Dokumen ini mendokumentasikan status sebenarnya tanpa klaim palsu (No Fabricated Data). Evaluator dan juri dapat memverifikasi status secara mandiri.

---

## 1. IBM watsonx.ai (Model Foundation: IBM Granite)

| Komponen | Status Saat Ini | Keterangan |
| :--- | :--- | :--- |
| **Kredensial** | `CONNECTION_FAILED` | `Gagal menghubungi endpoint watsonx: WMLClientError - Model 'ibm/granite-3-8b-instruct' is not supported for this environment. Supported models: ['ibm/gra` |
| **Model ID** | `ibm/granite-3-8b-instruct` | Standar: `ibm/granite-3-8b-instruct` |
| **Latensi Uji** | `—` | Nilai aktual saat probe dijalankan |
| **Panduan Aktivasi** | — | Pastikan API key, Project ID, dan kuota watsonx Cloud aktif. |

### Peran IBM watsonx dalam Arsitektur BidSentry:
- **Tingkat 1 (Local Engine)**: Menjalankan aturan deterministik Perpres 12/2021 secara 100% lokal, offline, dan tanpa LLM untuk kepatuhan regulasi mutlak.
- **Tingkat 2 (watsonx Granite Advisory)**: Bila diaktifkan oleh pengguna, model IBM Granite digunakan untuk *semantic document extraction* sekunder (misal: merangkum kualifikasi tenaga ahli dan SLA). Seluruh data disanitasi oleh modul PII masking sebelum dikirim.

---

## 2. IBM Bob / Langflow MCP (Model Context Protocol)

| Komponen | Status Saat Ini | Keterangan |
| :--- | :--- | :--- |
| **Konfigurasi MCP** | `CONFIG_PRESENT` | `Konfigurasi Bob MCP server terverifikasi di bob/mcp.json (transport stdio, target: Langflow port 7860).` |
| **Transport** | `stdio` | Standar MCP specification |
| **Target Eksekusi** | `langflow run --mcp-server` | Port 7860 |
| **Panduan Aktivasi** | — | Jalankan Langflow lokal di port 7860 untuk menghubungkan agentic MCP server. |

### Peran MCP dalam Arsitektur:
- Menjembatani agent LLM dengan tool pengadaan lokal BidSentry melalui protokol standar MCP.
- Memungkinkan IDE agentic (seperti IBM Bob / Claude Desktop) memanggil fungsi audit pengadaan secara terstruktur.

---

## 3. Komponen Pendukung Lainnya

- **Mesin Aturan Lokal**: `READY` (14 aturan deklaratif Perpres 12/2021 aktif secara deterministik dan offline).
- **Langflow Advisory**: Terintegrasi via HTTP REST client (`bidsentry/services/langflow_service.py`), mode opt-in dengan konfirmasi manual pengguna.
- **Composio Automation**: Integrasi kalender dan dokumen tender, mode human-in-the-loop (memerlukan persetujuan eksplisit sebelum menyiapkan aksi).
