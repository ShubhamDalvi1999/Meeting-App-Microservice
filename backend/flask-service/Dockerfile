FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared package first and install it
COPY meeting_shared /app/meeting_shared/
RUN pip install -e /app/meeting_shared/

# Copy service files
COPY backend/flask-service/requirements.txt .
COPY backend/flask-service/src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONPATH=/app/src:/app/meeting_shared
ENV FLASK_APP=src/app.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"] 