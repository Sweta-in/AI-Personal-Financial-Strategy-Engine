# ── MCP Servers Dockerfile ──
# One image, CMD overridden per server in docker-compose

FROM python:3.11-slim as builder

WORKDIR /build
COPY quant/requirements.txt ./quant/
COPY mcp_servers/requirements.txt ./mcp_servers/
COPY ml/requirements.txt ./ml/
COPY rag/requirements.txt ./rag/

RUN pip install --no-cache-dir --prefix=/install \
    -r quant/requirements.txt \
    -r mcp_servers/requirements.txt \
    -r ml/requirements.txt

# ── Runtime ──
FROM python:3.11-slim

RUN groupadd -r finengine && useradd -r -g finengine finengine

WORKDIR /app

COPY --from=builder /install /usr/local
COPY quant/ ./quant/
COPY mcp_servers/ ./mcp_servers/
COPY ml/ ./ml/
COPY rag/ ./rag/
COPY backend/app/schemas/ ./backend/app/schemas/

RUN chown -R finengine:finengine /app
USER finengine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

EXPOSE 8001 8002 8003 8004 8005 8006

# Default: loan MCP. Override with docker-compose command.
CMD ["python", "-m", "mcp_servers.loan_mcp.server"]
