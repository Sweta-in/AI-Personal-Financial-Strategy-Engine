# ---- Builder ----
FROM python:3.11-slim AS builder

WORKDIR /app

COPY mcp_servers/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime ----
FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /install /usr/local

COPY mcp_servers/ /app/mcp_servers/
COPY quant/ /app/quant/
COPY ml/ /app/ml/
COPY rag/ /app/rag/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# CMD is overridden per-service in docker-compose.yml
CMD ["python", "-m", "mcp_servers.loan_mcp.server"]
