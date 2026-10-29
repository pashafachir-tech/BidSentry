FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system bidsentry && adduser --system --ingroup bidsentry --no-create-home bidsentry
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bidsentry/ ./bidsentry/
COPY web/ ./web/
COPY config/ ./config/
COPY data/ ./data/
COPY langflow/ ./langflow/
COPY index.html server.py composio_dispatcher.py ./
COPY bob/ ./bob/
COPY .env.example ./

RUN touch /app/audit_log.jsonl && chown -R bidsentry:bidsentry /app
VOLUME ["/app/audit_log.jsonl"]
USER bidsentry

# Default is local loopback (127.0.0.1).
# To expose to external networks or Docker port-mapping, set HOST=0.0.0.0 AND configure
# BIDSENTRY_ACCESS_TOKEN=<your-secret-token>. The server will refuse to start on 0.0.0.0 without a token.
ENV HOST=127.0.0.1
ENV PORT=8000
ENV LANGFLOW_URL=http://host.docker.internal:7860
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
ENTRYPOINT ["python", "server.py"]
