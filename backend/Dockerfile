FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Build context is the repository root, so resolve the backend app files from
# the backend/ subdirectory instead of assuming they live at the project root.
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libpq5 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY backend/. .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "120"]
