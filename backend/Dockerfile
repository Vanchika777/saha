FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose default port
EXPOSE 5000

ENV FLASK_ENV=production
# Use shell form so $PORT environment variable is properly expanded
CMD python run.py