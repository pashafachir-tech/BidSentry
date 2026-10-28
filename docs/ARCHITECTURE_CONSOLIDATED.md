# Peta Arsitektur Terkonsolidasi (Canonical Architecture Map)

Dokumen ini mendokumentasikan topologi backend dan modul sistem **BidSentry v2.2** setelah konsolidasi arsitektur menyeluruh.

---

## 1. Titik Masuk Server (Single Canonical Entry Point)

Sebelumnya terdapat 4 berkas server (`server.py`, `asgi.py`, `app.py`, `http_server.py`). Telah dikonsolidasikan dengan pembagian tanggung jawab yang tegas:

```
┌────────────────────────────────────────────────────────┐
│ 1. server.py (Root Launcher CLI)                       │
│    - Pembungkus argparser ringan                       │
│    - Memanggil uvicorn.run(create_asgi_app())          │
├────────────────────────────────────────────────────────┤
│ 2. bidsentry/asgi.py (Definitive ASGI Transport)       │
│    - FastAPI factory: create_asgi_app()                │
│    - Lifespan: AsyncDatabase + ARQ/Redis Pool          │
│    - Middleware: Host header & Bearer Token Guard      │
│    - Native FastAPI Routers: v1_router + stream_router │
├────────────────────────────────────────────────────────┤
│ 3. bidsentry/app.py (Dependency Injection Container)   │
│    - Dataclass Application (IoC Wiring)                │
│    - Factory: create_application()                     │
├────────────────────────────────────────────────────────┤
│ 4. bidsentry/http_server.py (Deprecated Adapter)       │
│    - Mengeluarkan DeprecationWarning                   │
│    - Mendelegasikan eksekusi langsung ke create_asgi_app()
└────────────────────────────────────────────────────────┘
```

---

## 2. Konsolidasi Modul dan Sumber Kebenaran Tunggal (Single Source of Truth)

| Kategori | Modul Kanonikal | Status Modul Pendamping | Keterangan Konsolidasi |
| :--- | :--- | :--- | :--- |
| **Audit Finansial** | `bidsentry.audits.financial` | `financial_engine.py` (Re-export facade) | Seluruh kalkulasi aritmatika BoQ, Benford, dan pricing imbalance disatukan di `financial.py`. |
| **Layanan Audit** | `bidsentry.services.audit_service` | `comprehensive_audit_service.py` (Engine) | `AuditService` menyediakan facade terpadu `.audit()` (aturan deterministik) dan `.audit_comprehensive()` (10 modul forensik). |
| **Audit Trail & Log** | `bidsentry.lib.audit_log` | `bidsentry.core.audit_trail` (Re-exported) | `HashChainedAuditTrail` dan `AuditLog` diakses terpadu melalui `bidsentry.lib.audit_log`. |
| **Skema & Kontrak** | `bidsentry.schemas` | `bidsentry.types` (Re-export facade) | Seluruh skema request/response (`AuditRequest`, `ComprehensiveAuditRequest`, dsb.) tersedia di `bidsentry.schemas`. |
| **Integrasi IBM watsonx** | `bidsentry.services.watsonx_service` | `WatsonxService` | Modul mandiri kelas enterprise yang mengeksekusi model IBM Granite (`ibm/granite-3-8b-instruct`) dengan PII redaction otomatis sebelum transmisi. |

---

## 3. Integrasi Ekosistem IBM (watsonx.ai, Bob, Langflow)

```
                            ┌───────────────────────────────────┐
                            │     Dokumen Tender (PDF/DOCX)     │
                            └─────────────────┬─────────────────┘
                                              │
                                              ▼
                                ┌───────────────────────────┐
                                │ bidsentry/lib/pii.py      │
                                │ (Sensor NIK, NPWP, Rek.) │
                                └─────────────┬─────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      │                                               │
                      ▼                                               ▼
     ┌─────────────────────────────────┐             ┌──────────────────────────────────┐
     │ 1. Local Deterministic Core     │             │ 2. IBM watsonx.ai / Granite      │
     │    - bidsentry/evaluators/      │             │    - bidsentry/services/watsonx_ │
     │      engine.py                  │             │      service.py                  │
     │    - 15 Aturan Perpres 12/2021  │             │    - ibm/granite-3-8b-instruct   │
     │    - 100% Offline & Exact Span  │             │    - Langflow Flow + Bob MCP     │
     └────────────────┬────────────────┘             └────────────────┬─────────────────┘
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              │
                                              ▼
                                ┌───────────────────────────┐
                                │ Verbatim Quote Grounding  │
                                │ (Exact Substring Match)   │
                                └─────────────┬─────────────┘
                                              │
                                              ▼
                                ┌───────────────────────────┐
                                │  Human-in-the-Loop Review │
                                │  & Hash-Chained Trail     │
                                └───────────────────────────┘
```
