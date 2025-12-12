FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Prod: Use gunicorn for multi-worker
CMD ["gunicorn", "-w 4", "-b 0.0.0.0:8000", "app.main:app"]