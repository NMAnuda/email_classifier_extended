# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Avoid cache issues and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose the port
EXPOSE 8000

# Set environment variables for lower memory footprint
ENV TRANSFORMERS_NO_ADVISORY_WARNINGS=1
ENV TOKENIZERS_PARALLELISM=false

# Run Gunicorn with 1 worker and 2 threads
CMD ["gunicorn", "-w", "1", "--threads", "2", "-b", "0.0.0.0:8000", "main:app"]
