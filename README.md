# BidSentry

BidSentry is a local-first procurement document review workspace. It compares tender requirements with bidder evidence, reconciles addenda, calculates delay-penalty scenarios, and highlights text signals for a human reviewer. It does not verify government registries or decide legal compliance, bidder eligibility, collusion, or fraud.

## Run locally

Requires Python 3.11 or newer. Copy `.env.example` to `.env`, install dependencies, then start the server:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Open <http://127.0.0.1:8000>. The server binds to loopback by default. No frontend build step is required.

## Architecture

```text
web/                         Dashboard, API client, light/dark themes
bidsentry/api/               FastAPI routes, SSE, request limits
bidsentry/evaluators/        Unified deterministic and grounded evaluation
bidsentry/forensics/         Addendum comparison, entity and contract analysis
bidsentry/audits/            BoQ arithmetic, risk and penalty calculations
bidsentry/generators/        Clarification, evaluation and objection drafts
bidsentry/core/              ARQ worker, PDF defense, audit chain, database
langflow/tender_extraction_flow.json
data/sample_tenders/         Clearly labelled synthetic regression fixtures
tests/benchmark_eval.py      Measured local P/R/F1 and latency per page
```

The dashboard register contains audit metadata written to the local audit log (`audit_log.jsonl`). While full unparsed document text is not archived in the log, verbatim evidence quotations associated with findings are retained for traceability and objection draft generation. Active review payloads are maintained in browser memory and requested from the API on demand.

## Security and Authentication

- **Access Token:** Set `BIDSENTRY_ACCESS_TOKEN=<secret_token>` in `.env` to protect API endpoints. When configured, all `/api/*` routes (except `/api/health`) require `Authorization: Bearer <secret_token>` or a valid session cookie.
- **Loopback Enforcement:** When running without an access token, the server binds strictly to loopback (`127.0.0.1`) and validates the `Host` header to protect against DNS rebinding. The server refuses to start on non-loopback interfaces (e.g. `0.0.0.0`) unless `BIDSENTRY_ACCESS_TOKEN` is configured.
- **Sensitive Operations:** Operations affecting configuration (`/api/settings/integrations`), automated dispatch (`/api/dispatch`), and audit deletion (`DELETE /api/audits`) are guarded and only permitted from verified local browser origins or authenticated token bearers.
- **Data Retention & Privacy:** Old audit logs are automatically purged on startup based on `AUDIT_RETENTION_DAYS` (default: 90 days). External AI processing requires explicit reviewer consent, and all outbound document payloads undergo strict PII redaction (email, phone, bank account, NPWP, and NIK).

## Evaluation workflow

The audit form posts to `POST /api/v1/audit/evaluate`. The same engine backs the legacy `POST /api/audit` route and `server.evaluate_tender` helper. It validates the provided NPWP format, reads KSWP text status, checks SBU/NIB expiry dates, compares bid-bond amounts, compares warranty duration, reconciles original and addendum clauses, and parses delay-penalty clauses. These are text checks; the application does not query tax, licensing, or guarantee registries.

The executive summary shows a GO/NO-GO triage badge based on critical administrative gaps detected in the supplied text. GO means no such gap was detected; it is not proof of eligibility. The result also reports unresolved required evidence, source quotations, adendum changes, and measured engine time.

`POST /api/v1/audit/sanggahan-doc` creates a DOCX, PDF, HTML, or Markdown draft. It includes only quotations that are exact substrings of the source text supplied with the request. Reviewers must verify procedure, deadlines, facts, and legal citations before using a draft.

## Routes

- `POST /api/v1/audit/evaluate` — unified bidder-focused evaluation.
- `POST /api/v1/audit/comprehensive` — PDF metadata, hidden-text screening, BoQ arithmetic, quote grounding, vendor network signals, contract comparison, legal-reference candidates, and hash-chain record.
- `POST /api/v1/audit/sanggahan-doc` — formal, source-grounded objection draft.
- `POST /api/v1/audit/clarification-doc` and `POST /api/v1/audit/minutes-eval-doc` — editable review document drafts.
- `POST /api/v1/audit/jobs` — queue a comprehensive audit with ARQ and Redis.
- `GET /api/v1/audit/jobs/{job_id}` and `GET /api/v1/audit/stream/{job_id}` — job state and SSE progress.
- `GET /api/overview` and `GET /api/audits` — locally recorded audit metadata.
- `POST /api/dispatch` — run configured Composio actions; when not configured, returns unavailable and creates no artifact.

For queue-backed work, run Redis and the API, then start `arq bidsentry.core.worker.WorkerSettings`. Set the same `REDIS_URL`, `AUDIT_QUEUE_NAME`, and `DATABASE_URL` for the API and worker. SQLite is the local database default; PostgreSQL is supported.

## Optional structured extraction

External processing is disabled unless the reviewer checks the consent box. When configured, an enabled Langflow flow is tried first. Otherwise set `LLM_PROVIDER` to `openai`, `gemini`, or `watsonx`, and set `LLM_API_KEY`, `LLM_MODEL_NAME`, and `WATSONX_PROJECT_ID` where applicable. Legacy `GEMINI_API_KEY` and `GEMINI_MODEL` are supported. Structured responses are Pydantic-validated, and every returned quote is checked locally against supplied document text.

Import `langflow/tender_extraction_flow.json` into Langflow and configure its Language Model component with an authorized provider. Then set `LANGFLOW_ENABLED=true`, `LANGFLOW_URL`, `LANGFLOW_FLOW_ID`, and the application token/API key if required. The flow extracts scope, addendum changes, personnel qualifications, and SLA text; it does not decide eligibility.

The local **Koneksi layanan** settings panel has a read-only **Tes koneksi** action. It checks access to the selected Langflow flow and lists Composio connected-account metadata; it does not run the flow or create Google Docs, calendar events, or Gmail drafts. Configure `COMPOSIO_API_KEY` and `COMPOSIO_USER_ID` for the Composio project, then connect the required Google toolkits to that user in Composio. BidSentry uses the Composio v3.1 tool execution API; live actions run only after the reviewer checks the confirmation box. An optional Gmail draft is created only when an email address is provided; messages are never sent.

## Penalty assumptions and regulation

The calculator reads the rate and cap from the supplied contract clause. It compares scenarios with 1‰ per day and displays a 5% capped scenario as an explicitly illustrative assumption, not a universal statutory cap. Verify the applicable procurement regulation and contract wording for the tender date. The LKPP consolidated text lists a 1‰ per-day delay fine in the relevant provision; the implementation does not infer a 5% legal cap.

## Benchmark

Run the benchmark and its assertions with:

```powershell
python -m pytest tests/benchmark_eval.py -v -s
```

The real-source slice below uses one publicly indexed [LPSE package listing](https://spse.inaproc.id/kemkes/nontender/10261197000/pengumumanpl), captured as a short text excerpt in `data/public_lpse/`. The labels cover only two supported local checks explicitly present in that listing: SBU and confirmation of taxpayer status. A maintainer mapped those two labels from the source text; there is no bidder response, no compliance verdict, and no independent second annotation. The attached detailed-work description was not included in this sample. Latency is the mean of 25 evaluator runs after one warm-up per fixture.

| Dataset | Source pages | Supported labels | TP / FP / FN | Precision | Recall | F1 | Measured latency/page |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Public LPSE listing, package 10261197000 | 1 | 2 | 2 / 0 / 0 | 100% | 100% | 100% | 0.050 ms |

These are measured results for one short portal page and two labels, not a representative procurement benchmark. They do not support a general accuracy claim such as “over 94%.” The synthetic regression figures are reported separately by the same command and must not be combined with the LPSE row. Latency covers the local text evaluator only, not PDF extraction, OCR, network transfer, or AI-provider calls.
