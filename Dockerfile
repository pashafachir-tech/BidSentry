# ─── BidSentry — Containerised Bridge Server ──────────────────────────────────
# Build:   docker build -t bidsentry .
# Run:     docker run -p 8000:8000 --env-file .env bidsentry
#
# The container serves index.html and proxies /api/* to Langflow.
# Langflow itself is expected to run on the host or a separate container;
# set LANGFLOW_HOST accordingly (e.g. http://host-gateway:7860 on Linux,
# or http://host.docker.internal:7860 on Docker Desktop Mac/Windows).
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── Metadata ──────────────────────────────────────────────────────────────────
LABEL maintainer="BidSentry Team"
LABEL description="BidSentry Bridge Server — REST proxy + Composio dispatcher"
LABEL version="1.0.0"

# ── OS hardening: no root at runtime ──────────────────────────────────────────
RUN addgroup --system bidsentry \
 && adduser  --system --ingroup bidsentry --no-create-home bidsentry

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Copy only necessary files (no .env, no node_modules, no __pycache__) ──────
COPY server.py               ./server.py
COPY composio_dispatcher.py  ./composio_dispatcher.py
COPY verify_system.py        ./verify_system.py
COPY index.html              ./index.html
COPY sample-data/            ./sample-data/

# ── No third-party pip deps — stdlib only ─────────────────────────────────────
# (If you later add requirements.txt, uncomment the two lines below)
# COPY requirements.txt ./requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# ── Ensure audit log directory is writable by the service user ────────────────
RUN touch /app/audit_log.jsonl \
 && chown bidsentry:bidsentry /app/audit_log.jsonl \
 && chown -R bidsentry:bidsentry /app

# ── Drop privileges ───────────────────────────────────────────────────────────
USER bidsentry

# ── Runtime environment defaults (override via --env-file .env or -e) ─────────
ENV BRIDGE_PORT=8000
ENV LANGFLOW_HOST=http://host.docker.internal:7860

# ── Expose bridge port ────────────────────────────────────────────────────────
EXPOSE 8000

# ── Health check: verify bridge is responding ─────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" \
  || exit 1

# ── Entrypoint ────────────────────────────────────────────────────────────────
ENTRYPOINT ["python", "server.py"]
CMD ["--port", "8000"]
