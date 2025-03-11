FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/meeting_shared /app/src /app/logs

# Copy requirements first to leverage Docker cache
COPY backend/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app/src:/app/meeting_shared
ENV FLASK_APP=src/app.py
ENV FLASK_ENV=development
ENV SERVICE_TYPE=auth

# Create entrypoint script
COPY backend/auth-service/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

EXPOSE 5001

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"] 