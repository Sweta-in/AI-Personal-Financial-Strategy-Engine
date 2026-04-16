# ── Backend Dockerfile ──
# Multi-stage: builder → slim runtime

FROM python:3.11-slim as builder

WORKDIR /build
COPY backend/requirements.txt ./backend/
COPY quant/requirements.txt ./quant/
COPY agents/requirements.txt ./agents/
COPY rag/requirements.txt ./rag/
COPY ml/requirements.txt ./ml/
COPY mcp_servers/requirements.txt ./mcp_servers/

RUN pip install --no-cache-dir --prefix=/install \
    -r backend/requirements.txt \
    -r quant/requirements.txt \
    -r agents/requirements.txt \
    -r rag/requirements.txt

# ── Runtime ──
FROM python:3.11-slim

RUN groupadd -r finengine && useradd -r -g finengine finengine

WORKDIR /app

COPY --from=builder /install /usr/local
COPY backend/ ./backend/
COPY quant/ ./quant/
COPY agents/ ./agents/
COPY rag/ ./rag/
COPY ml/ ./ml/
COPY mcp_servers/ ./mcp_servers/

RUN chown -R finengine:finengine /app
USER finengine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
