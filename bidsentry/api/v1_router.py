"""FastAPI router for versioned forensic audits and generated review drafts."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from bidsentry.api.routes import ApiRouter
from bidsentry.app import Application
from bidsentry.core.database import AsyncDatabase, serialize_job
from bidsentry.core.job_events import publish_job_event
from bidsentry.schemas.audit_contracts import AuditJobCreated
from bidsentry.schemas.comprehensive import ComprehensiveAuditRequest
from bidsentry.types.responses import failure, success


LOGGER = logging.getLogger("bidsentry.api.v1")


def create_v1_router(application: Application) -> APIRouter:
    """Expose v1 operations through the same validated service contract."""
    router = APIRouter(prefix="/api/v1", tags=["forensic-audit-v1"])
    dispatch = ApiRouter(application)

    @router.post("/audit/comprehensive")
    async def comprehensive_audit(request: Request) -> JSONResponse:
        payload, error = await _json_payload(request, application.settings.max_request_bytes)
        if error is not None:
            return error
        result = await run_in_threadpool(dispatch.dispatch, "POST", "/api/v1/audit/comprehensive", "", payload)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers or {})

    @router.post("/audit/evaluate")
    async def evaluate_tender(request: Request) -> JSONResponse:
        payload, error = await _json_payload(request, application.settings.max_request_bytes)
        if error is not None:
            return error
        result = await run_in_threadpool(dispatch.dispatch, "POST", "/api/v1/audit/evaluate", "", payload)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers or {})

    @router.post("/audit/sanggahan-doc")
    async def sanggahan_document(request: Request) -> JSONResponse:
        payload, error = await _json_payload(request, application.settings.max_request_bytes)
        if error is not None:
            return error
        result = await run_in_threadpool(dispatch.dispatch, "POST", "/api/v1/audit/sanggahan-doc", "", payload)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers or {})

    @router.post("/audit/clarification-doc")
    async def clarification_document(request: Request) -> JSONResponse:
        payload, error = await _json_payload(request, application.settings.max_request_bytes)
        if error is not None:
            return error
        result = await run_in_threadpool(dispatch.dispatch, "POST", "/api/v1/audit/clarification-doc", "", payload)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers or {})

    @router.post("/audit/minutes-eval-doc")
    async def minutes_document(request: Request) -> JSONResponse:
        payload, error = await _json_payload(request, application.settings.max_request_bytes)
        if error is not None:
            return error
        result = await run_in_threadpool(dispatch.dispatch, "POST", "/api/v1/audit/minutes-eval-doc", "", payload)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers or {})

    @router.post("/audit/jobs", status_code=202)
    async def create_audit_job(request: Request) -> JSONResponse:
        request_id = str(uuid.uuid4())
        raw_payload, error = await _json_payload(request, application.settings.max_request_bytes)
        if error is not None:
            return error
        try:
            audit_request = ComprehensiveAuditRequest.model_validate(raw_payload)
        except ValidationError as exc:
            details = [
                {
                    "field": ".".join(str(part) for part in item["loc"]),
                    "message": item["msg"],
                }
                for item in exc.errors(include_url=False, include_input=False)
            ]
            return JSONResponse(
                failure("INVALID_REQUEST", "The audit request failed schema validation.", request_id, details),
                status_code=422,
            )

        database: AsyncDatabase | None = getattr(request.app.state, "database", None)
        redis = getattr(request.app.state, "redis_pool", None)
        job_settings = getattr(request.app.state, "job_settings", None)
        if database is None or redis is None or job_settings is None:
            return JSONResponse(
                failure("JOB_ENGINE_UNAVAILABLE", "The asynchronous audit engine is not available.", request_id),
                status_code=503,
                headers={"Retry-After": "5"},
            )

        payload = audit_request.model_dump(mode="json")
        canonical_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        job_id = str(uuid.uuid4())
        try:
            await database.create_job(
                job_id=job_id,
                tender_id=audit_request.tender_id,
                vendor_id=audit_request.vendor_id,
                payload_sha256=hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest(),
            )
        except Exception:
            LOGGER.exception("Could not persist procurement audit job", extra={"job_id": job_id})
            return JSONResponse(
                failure("JOB_PERSISTENCE_FAILED", "The audit job could not be stored.", request_id),
                status_code=503,
                headers={"Retry-After": "5"},
            )

        try:
            await publish_job_event(redis, job_id, {
                "status": "queued",
                "progress": 0,
                "stage": "queued",
            })
            queued_job = await redis.enqueue_job(
                "execute_procurement_audit_job",
                job_id,
                payload,
                _job_id=job_id,
                _queue_name=job_settings.audit_queue_name,
                _expires=max(
                    job_settings.audit_job_result_ttl_seconds,
                    job_settings.audit_job_timeout_seconds * 4,
                ),
            )
            if queued_job is None:
                raise RuntimeError("ARQ reported a duplicate identifier for a newly created job.")
        except Exception:
            LOGGER.exception("Could not enqueue procurement audit", extra={"job_id": job_id})
            try:
                await database.update_job(
                    job_id,
                    status="failed",
                    progress=100,
                    stage="failed",
                    error_code="QUEUE_UNAVAILABLE",
                    error_message="The audit could not be added to the worker queue.",
                )
            except Exception:
                LOGGER.exception("Could not persist queue failure", extra={"job_id": job_id})
            return JSONResponse(
                failure("QUEUE_UNAVAILABLE", "The audit could not be added to the worker queue.", request_id),
                status_code=503,
                headers={"Retry-After": "5"},
            )

        created = AuditJobCreated(
            job_id=job_id,
            status="queued",
            status_url=f"/api/v1/audit/jobs/{job_id}",
            stream_url=f"/api/v1/audit/stream/{job_id}",
        )
        return JSONResponse(success(created.model_dump(mode="json"), request_id), status_code=202)

    @router.get("/audit/jobs/{job_id}")
    async def get_audit_job(job_id: str, request: Request) -> JSONResponse:
        request_id = str(uuid.uuid4())
        database: AsyncDatabase | None = getattr(request.app.state, "database", None)
        if database is None:
            return JSONResponse(
                failure("JOB_ENGINE_UNAVAILABLE", "The asynchronous audit engine is not available.", request_id),
                status_code=503,
            )
        record = await database.get_job(job_id)
        if record is None:
            return JSONResponse(failure("JOB_NOT_FOUND", "Audit job was not found.", request_id), status_code=404)
        return JSONResponse(success(serialize_job(record), request_id), status_code=200)

    return router


async def _json_payload(request: Request, maximum: int) -> tuple[object, JSONResponse | None]:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
    if content_type != "application/json":
        request_id = str(uuid.uuid4())
        return None, JSONResponse(failure("UNSUPPORTED_MEDIA_TYPE", "Content-Type must be application/json.", request_id), status_code=415)
    body = bytearray()
    try:
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > maximum:
                request_id = str(uuid.uuid4())
                return None, JSONResponse(failure("PAYLOAD_TOO_LARGE", "Request body exceeds the configured limit.", request_id), status_code=413)
        payload = json.loads(body.decode("utf-8")) if body else {}
        return payload, None
    except (UnicodeDecodeError, json.JSONDecodeError):
        request_id = str(uuid.uuid4())
        return None, JSONResponse(failure("INVALID_JSON", "Request body must be valid UTF-8 JSON.", request_id), status_code=400)
