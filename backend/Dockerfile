FROM python:3.11-slim

WORKDIR /app

# copy backend code
COPY . /app

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# run Flask app
CMD ["python", "-m", "flask", "--app", "app.main:app", "run", "--host", "0.0.0.0", "--port", "8000"]
