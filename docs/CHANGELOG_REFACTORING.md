# Changelog refactoring

## 2.1 — Audit evidence and upload reliability

- Changed custom keyword matches to review signals so a missing keyword is not represented as automatic noncompliance and a present keyword is not represented as verified fulfillment.
- Added source filename and extracted-text line references to custom audit findings, plus separate requirement and evidence excerpts.
- Preserved successfully extracted files in a mixed-result multi-file upload and kept per-file extraction errors visible in the upload form.
- Clarified that text line references are not PDF page references and that scanned PDFs need OCR.

## 2.0 — Modular local review workspace

### Architecture

- Replaced the single HTTP handler/business-logic module with `bidsentry/api`, `controllers`, `services`, `lib`, and `types` packages.
- Kept `server.py` as a small CLI entry point and preserved `run_rules_engine()` as a compatibility adapter.
- Centralized bind settings, request limits, audit-log paths, Langflow configuration, and Composio configuration in `bidsentry/config.py` and `.env.example`.
- Added explicit API routes for health, overview, audit search, JSON export, document audit, and workspace dispatch.
- Standardized API success and error envelopes; malformed JSON, invalid fields, oversized payloads, unsupported methods, and unknown routes receive stable errors.

### Audit and integrations

- Moved rule matching out of the browser into `AuditService`; browser code now submits documents to the backend instead of maintaining a second parser.
- Added a consistent 0–100 deterministic risk triage score with Low, Medium, High, and Critical bands, driver explanations, and an explicit uncalibrated-score disclosure.
- Added contract review signals for unbounded penalty text, conditional/late payment terms, and mixed budget-source references. These are prompts for human review, not fraud findings.
- Added an opt-in Langflow advisory adapter using the configured flow run endpoint. The local rules result remains available when Langflow is disabled, missing, or unavailable.
- Kept Composio actions in a service facade with simulation fallback, and changed audit logging to store metadata only rather than document payloads.
- Added a health response that distinguishes configured MCP metadata from a verified live IBM Bob connection.

### UI/UX

- Replaced the large inline dashboard with a small HTML shell and local ES modules for API access, UI state, rendering, and interactions.
- Applied a restrained editorial layout informed by the supplied Lovelace theme: neutral canvas, fine dividers, rounded cards, compact status colors, and responsive navigation.
- Added an executive overview, filterable procurement register, risk detail panel, contract findings, explicit synthetic-data labels, new-audit dialog, and JSON export.
- Connected search/filtering, audit scans, export, health status, and Composio follow-up to the backend.

### Validation boundary

- The sample portfolio is explicitly labelled synthetic. No real-user feedback or live IBM Bob/Langflow flow is claimed by this refactor.
- The supplied archive is a Home Assistant Lovelace integration. Its YAML and bundled JavaScript were inspected as reference material and are not application dependencies.
