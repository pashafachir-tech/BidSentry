"""FastAPI transport adapter over the existing application services and API contract."""

from __future__ import annotations

import ipaddress
import json
import logging
import mimetypes
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from arq import create_pool
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.middleware.base import RequestResponseEndpoint
from starlette.concurrency import run_in_threadpool

from bidsentry.api.routes import ApiResponse, ApiRouter
from bidsentry.api.stream import router as audit_stream_router
from bidsentry.api.v1_router import create_v1_router
from bidsentry.app import create_application
from bidsentry.config import Settings
from bidsentry.core.config import AsyncEngineSettings
from bidsentry.core.database import AsyncDatabase
from bidsentry.core.worker import (
    build_redis_settings,
    deserialize_job_definition,
    serialize_job_definition,
)
from bidsentry.types.responses import failure


LOGGER = logging.getLogger("bidsentry.asgi")
API_METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    "Cache-Control": "no-store",
}


def create_asgi_app(settings: Settings | None = None) -> FastAPI:
    application = create_application(settings)
    router = ApiRouter(application)

    @asynccontextmanager
    async def lifespan(api: FastAPI) -> AsyncIterator[None]:
        job_settings = AsyncEngineSettings()
        database = AsyncDatabase(job_settings.database_url, echo=job_settings.database_echo)
        await database.initialize()
        api.state.job_settings = job_settings
        api.state.database = database
        api.state.redis_pool = None
        try:
            api.state.redis_pool = await create_pool(
                build_redis_settings(job_settings.redis_url),
                retry=0,
                default_queue_name=job_settings.audit_queue_name,
                job_serializer=serialize_job_definition,
                job_deserializer=deserialize_job_definition,
            )
        except Exception:
            LOGGER.exception("Redis job queue unavailable; async audit endpoints will return 503")
        try:
            yield
        finally:
            redis_pool = getattr(api.state, "redis_pool", None)
            try:
                if redis_pool is not None:
                    await redis_pool.aclose()
            except Exception:
                LOGGER.exception("Could not close Redis job queue cleanly")
            finally:
                await database.dispose()

    api = FastAPI(
        title="BidSentry API",
        version="2.2",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    api.include_router(create_v1_router(application))
    api.include_router(audit_stream_router)

    @api.middleware("http")
    async def apply_security_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response

    @api.api_route("/", methods=API_METHODS, include_in_schema=False)
    @api.api_route("/{url_path:path}", methods=API_METHODS, include_in_schema=False)
    async def dispatch(request: Request, url_path: str = "") -> Response:
        request_id = str(uuid.uuid4())
        path = request.url.path
        if path == "/" or path.startswith("/web/"):
            return _static_response(application.settings, path)

        if path in {"/api/settings/integrations"} and request.method in {"PUT", "POST"} and not _is_local_settings_request(request, application.settings.port):
            return JSONResponse(failure("FORBIDDEN", "Pengaturan hanya dapat diubah dari browser lokal.", request_id), status_code=403)

        try:
            if path == "/api/documents/extract" and request.method == "POST":
                body = await _read_limited(request, 8 * 1024 * 1024)
                query = urllib.parse.parse_qs(request.url.query, keep_blank_values=True)
                filename = query.get("filename", [""])[0]
                payload = {"filename": filename, "content": body}
            else:
                if request.method in {"POST", "PUT", "DELETE"}:
                    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().casefold()
                    raw = await _read_limited(request, application.settings.max_request_bytes)
                    if raw and content_type == "application/json":
                        payload = json.loads(raw.decode("utf-8"))
                    elif raw and content_type != "application/json":
                        return JSONResponse(failure("UNSUPPORTED_MEDIA_TYPE", "Content-Type must be application/json.", request_id), status_code=415)
                    else:
                        payload = {} if request.method in {"POST", "PUT"} else None
                else:
                    payload = None
            result: ApiResponse = await run_in_threadpool(
                router.dispatch,
                request.method,
                path,
                request.url.query,
                payload,
            )
            return JSONResponse(result.body, status_code=result.status, headers=result.headers or {})
        except OverflowError:
            return JSONResponse(failure("PAYLOAD_TOO_LARGE", "Request body exceeds the configured limit.", request_id), status_code=413)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JSONResponse(failure("INVALID_JSON", "Request body must be valid UTF-8 JSON.", request_id), status_code=400)
        except ValueError as exc:
            return JSONResponse(failure("INVALID_REQUEST", str(exc), request_id), status_code=400)
        except Exception:
            LOGGER.exception("ASGI transport request %s failed on %s %s", request_id, request.method, path)
            return JSONResponse(failure("INTERNAL_ERROR", "The request could not be completed.", request_id), status_code=500)

    return api


async def _read_limited(request: Request, maximum: int) -> bytes:
    length = request.headers.get("content-length")
    if length is not None:
        try:
            if int(length) < 0:
                raise ValueError("Content-Length must be non-negative.")
            if int(length) > maximum:
                raise OverflowError
        except ValueError as exc:
            raise ValueError("Content-Length must be a valid non-negative integer.") from exc
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > maximum:
            raise OverflowError
        chunks.append(chunk)
    return b"".join(chunks)


def _static_response(settings: Settings, url_path: str) -> Response:
    if url_path == "/":
        candidate, root = settings.workspace_root / "index.html", settings.workspace_root.resolve()
    elif url_path.startswith("/web/"):
        candidate, root = settings.static_root / url_path[len("/web/"):], settings.static_root.resolve()
    else:
        return JSONResponse(failure("NOT_FOUND", "Resource was not found.", ""), status_code=404)
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return JSONResponse(failure("FORBIDDEN", "Resource path is not allowed.", ""), status_code=403)
    if not resolved.is_file():
        return JSONResponse(failure("NOT_FOUND", "Resource was not found.", ""), status_code=404)
    content_type, _ = mimetypes.guess_type(resolved.name)
    if resolved.suffix == ".js":
        content_type = "text/javascript"
    return FileResponse(resolved, media_type=content_type, headers={"Cache-Control": "no-store"})


def _is_local_settings_request(request: Request, configured_port: int) -> bool:
    client_host = request.client.host if request.client else ""
    try:
        if not ipaddress.ip_address(client_host).is_loopback:
            return False
    except ValueError:
        return False
    host = urllib.parse.urlsplit("//" + request.headers.get("host", ""))
    allowed_hosts = {"localhost", "127.0.0.1", "::1"}
    if host.hostname not in allowed_hosts or host.username or host.password:
        return False
    try:
        if (host.port or 80) != configured_port:
            return False
    except ValueError:
        return False
    origin = request.headers.get("origin")
    if not origin:
        return True
    parsed = urllib.parse.urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
        return False
    try:
        origin_port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError:
        return False
    return parsed.hostname == host.hostname and origin_port == configured_port
