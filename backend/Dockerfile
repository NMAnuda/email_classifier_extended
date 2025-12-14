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

# Install gunicorn in final stage
RUN pip install --no-cache-dir gunicorn==21.2.0

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Gunicorn: 1 worker to avoid out-of-memory
CMD ["python", "-m", "gunicorn", "-w", "1", "--threads", "2", "-b", "0.0.0.0:8000", "app.main:app"]
