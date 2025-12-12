# Multi-stage: Build heavy deps in first stage, slim runtime in second
FROM python:3.12-slim as builder

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy & install deps (heavy stuff here)
COPY requirements.txt .
# CPU-only for torch (avoids GPU bloat)
ENV PIP_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --target=/install -r requirements.txt

# Final slim stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed deps from builder (no bloat)
COPY --from=builder /install /usr/local/lib/python3.12/site-packages

# Copy app code (light)
COPY . .

# Optional: Pre-download models to speed startup (reduces runtime size)
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"

EXPOSE 8000

# Prod CMD
CMD ["gunicorn", "-w 4", "-b 0.0.0.0:8000", "app.main:app"]