# -------------------------------
# Stage 1: Build heavy deps
# -------------------------------
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies needed for building packages
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install into a separate folder
COPY requirements.txt .
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --target=/install -r requirements.txt

# -------------------------------
# Stage 2: Slim runtime
# -------------------------------
FROM python:3.12-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local/lib/python3.12/site-packages

# Copy executables from builder (bin dir for tools)
COPY --from=builder /usr/local/bin /usr/local/bin

# Install gunicorn in final stage (no chmod needed)
RUN pip install --no-cache-dir gunicorn==21.2.0

# Copy your application code
COPY . .

# Optional: Pre-download models to reduce startup time
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"

# Expose port
EXPOSE 8000

# Fixed: Clean exec form CMD (no trailing comma, 1 worker for OOM)
CMD ["python", "-m", "gunicorn", "app.main:app", "--workers", "1", "--bind", "0.0.0.0:8000"]