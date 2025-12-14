# Multi-stage: Build heavy deps in first stage, slim runtime in second
FROM python:3.12-slim as builder

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy & install deps
COPY requirements.txt .
# CPU-only for torch (extra index—falls back to PyPI)
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --target=/install -r requirements.txt

# Final slim stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed deps from builder
COPY --from=builder /install /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin  # Bin for tools

# Copy app code
COPY . .

# Optional: Pre-download models (speeds startup, ~2GB load)
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"

EXPOSE 8000

# Fixed: Use python -m gunicorn (module run—no bin PATH issue, 1 worker for RAM)
CMD ["python", "-m", "gunicorn", "app.main:app", "--workers=1", "--bind=0.0.0.0:8000"]