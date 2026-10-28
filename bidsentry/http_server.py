"""Legacy HTTP transport module (Deprecated).

The canonical server entry points for BidSentry are:
- `server.py`: CLI wrapper for development and local execution.
- `bidsentry/asgi.py`: Official FastAPI ASGI transport application.
"""

from __future__ import annotations

import warnings
from bidsentry.app import Application
from bidsentry.asgi import create_asgi_app


def serve(app: Application) -> None:
    """Legacy server starter. Delegates to uvicorn + ASGI app."""
    warnings.warn(
        "bidsentry.http_server.serve is deprecated. Use `server.py` or `bidsentry.asgi.create_asgi_app`.",
        DeprecationWarning,
        stacklevel=2,
    )
    import uvicorn
    uvicorn.run(create_asgi_app(app.settings), host=app.settings.host, port=app.settings.port)
