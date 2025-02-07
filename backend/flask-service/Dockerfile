FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=src.app
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    redis-tools \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts first
COPY scripts/migrate.sh /migrate.sh
RUN chmod +x /migrate.sh

# Create and set permissions for the entrypoint script
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Run migrations' >> /entrypoint.sh && \
    echo '/migrate.sh' >> /entrypoint.sh && \
    echo '' >> /entrypoint.sh && \
    echo '# Start the application' >> /entrypoint.sh && \
    echo 'gunicorn --bind 0.0.0.0:5000 "src:app"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Copy the rest of the application
COPY . .

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"] 