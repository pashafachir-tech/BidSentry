"""HTTP transport: request parsing, static serving, and response writing only."""

from __future__ import annotations

import ipaddress
import json
import mimetypes
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from bidsentry.api.routes import ApiResponse, ApiRouter
from bidsentry.app import Application
from bidsentry.types.responses import failure


class BidSentryHandler(BaseHTTPRequestHandler):
    app: Application
    router: ApiRouter

    def log_message(self, format: str, *args: Any) -> None:
        if args and len(args) > 1 and str(args[1]).startswith(("4", "5")):
            # Avoid logging paths and query strings, which may contain a user's filename.
            super().log_message("HTTP error response %s", args[1])

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path.startswith("/api/"):
            self._api("GET", parsed.path, parsed.query)
        else:
            self._static(parsed.path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        self._api("POST", parsed.path, parsed.query)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_PUT(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path.startswith("/api/"):
            self._api("PUT", parsed.path, parsed.query)
        else:
            self._method_not_allowed()

    def do_PATCH(self) -> None:
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        self._method_not_allowed()

    def _api(self, method: str, path: str, query: str) -> None:
        request_id = str(uuid.uuid4())
        try:
            if method in {"GET", "PUT"} and path == "/api/settings/integrations" and not self._is_local_settings_request():
                self._send_json(ApiResponse(403, failure("LOCAL_ONLY", "Pengaturan integrasi hanya dapat diakses dari browser lokal.", request_id)))
                return
            if method == "POST" and path == "/api/dispatch" and not self._is_local_settings_request():
                self._send_json(ApiResponse(403, failure("LOCAL_ONLY", "Tindakan workspace hanya dapat dikirim dari browser lokal.", request_id)))
                return
            if method == "POST" and path == "/api/review-feedback" and not self._is_local_settings_request():
                self._send_json(ApiResponse(403, failure("LOCAL_ONLY", "Catatan reviewer hanya dapat dikirim dari browser lokal.", request_id)))
                return
            if method in {"POST", "PUT"} and path == "/api/documents/extract":
                if self.headers.get_content_type() != "application/octet-stream":
                    self._send_json(ApiResponse(415, failure("UNSUPPORTED_MEDIA_TYPE", "Content-Type must be application/octet-stream.", request_id)))
                    return
                params = urllib.parse.parse_qs(query, keep_blank_values=True)
                filename = params.get("filename", [""])[0]
                body = {"filename": filename, "content": self._read_document_bytes()}
            else:
                if method in {"POST", "PUT"} and self.headers.get_content_type() != "application/json":
                    self._send_json(ApiResponse(415, failure("UNSUPPORTED_MEDIA_TYPE", "Content-Type must be application/json.", request_id)))
                    return
                body = self._read_json() if method in {"POST", "PUT"} else None
            response = self.router.dispatch(method, path, query, body)
        except OverflowError:
            response = ApiResponse(413, failure("PAYLOAD_TOO_LARGE", "Request body exceeds the configured limit.", request_id))
        except (UnicodeDecodeError, json.JSONDecodeError):
            response = ApiResponse(400, failure("INVALID_JSON", "Request body must be valid UTF-8 JSON.", request_id))
        except ValueError as exc:
            response = ApiResponse(400, failure("INVALID_REQUEST", str(exc), request_id))
        self._send_json(response)

    def _read_json(self) -> Any:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("Content-Length must be a non-negative integer.") from exc
        if length < 0:
            raise ValueError("Content-Length must be a non-negative integer.")
        if length > self.app.settings.max_request_bytes:
            raise OverflowError
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _is_local_settings_request(self) -> bool:
        try:
            if not ipaddress.ip_address(self.client_address[0]).is_loopback:
                return False
        except ValueError:
            return False
        host = urllib.parse.urlsplit("//" + self.headers.get("Host", ""))
        allowed_hosts = {"localhost", "127.0.0.1", "::1"}
        if host.hostname not in allowed_hosts or host.username or host.password:
            return False
        try:
            host_port = host.port or 80
        except ValueError:
            return False
        if host_port != self.app.settings.port:
            return False
        origin = self.headers.get("Origin")
        if not origin:
            return True
        parsed_origin = urllib.parse.urlsplit(origin)
        if parsed_origin.scheme not in {"http", "https"} or parsed_origin.path or parsed_origin.query or parsed_origin.fragment or parsed_origin.username:
            return False
        try:
            origin_port = parsed_origin.port or (443 if parsed_origin.scheme == "https" else 80)
        except ValueError:
            return False
        return parsed_origin.hostname == host.hostname and origin_port == host_port

    def _read_document_bytes(self) -> bytes:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("Content-Length must be a non-negative integer.") from exc
        if length < 0:
            raise ValueError("Content-Length must be a non-negative integer.")
        if length > 8 * 1024 * 1024:
            raise OverflowError
        return self.rfile.read(length) if length else b""

    def _static(self, url_path: str) -> None:
        if url_path in {"", "/"}:
            candidate = self.app.settings.workspace_root / "index.html"
        elif url_path.startswith("/web/"):
            candidate = self.app.settings.static_root / url_path[len("/web/"):]
        else:
            self._send_json(ApiResponse(404, failure("NOT_FOUND", "Resource was not found.", "")))
            return
        root = (self.app.settings.workspace_root if url_path in {"", "/"} else self.app.settings.static_root).resolve()
        path = candidate.resolve()
        try:
            path.relative_to(root)
        except ValueError:
            self._send_json(ApiResponse(403, failure("FORBIDDEN", "Resource path is not allowed.", "")))
            return
        if not path.is_file():
            self._send_json(ApiResponse(404, failure("NOT_FOUND", "Resource was not found.", "")))
            return
        try:
            content = path.read_bytes()
        except OSError:
            self._send_json(ApiResponse(404, failure("NOT_FOUND", "Resource was not found.", "")))
            return
        mime, _ = mimetypes.guess_type(path.name)
        if path.suffix == ".js":
            mime = "text/javascript"
        self.send_response(200)
        self.send_header("Content-Type", (mime or "application/octet-stream") + ("; charset=utf-8" if mime and mime.startswith(("text/", "application/javascript")) else ""))
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, response: ApiResponse) -> None:
        body = json.dumps(response.body, ensure_ascii=False).encode("utf-8")
        self.send_response(response.status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        for key, value in (response.headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        )

    def _method_not_allowed(self) -> None:
        self._send_json(ApiResponse(405, failure("METHOD_NOT_ALLOWED", "HTTP method is not supported.", "")))


def serve(app: Application) -> None:
    router = ApiRouter(app)
    handler = type("ConfiguredBidSentryHandler", (BidSentryHandler,), {"app": app, "router": router})
    server = ThreadingHTTPServer((app.settings.host, app.settings.port), handler)
    print(f"BidSentry 2.1 | http://{app.settings.host}:{app.settings.port}")
    print(f"Local rules ready | Langflow: {'enabled' if app.settings.langflow_configured else 'local fallback'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBidSentry stopped.")
    finally:
        server.server_close()
