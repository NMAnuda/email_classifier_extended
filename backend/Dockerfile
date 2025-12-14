FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

EXPOSE 8000

# Gunicorn with 1 worker + 2 threads
CMD ["python", "-m", "gunicorn", "-w", "1", "--threads", "2", "-b", "0.0.0.0:8000", "app.main:app"]
