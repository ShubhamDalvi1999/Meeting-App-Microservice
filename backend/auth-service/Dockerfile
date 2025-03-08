FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install APScheduler==3.10.4

# Create necessary directories
RUN mkdir -p /app/migrations/versions /app/logs /app/src /app/scripts /app/instance /app/shared

# Copy files by directory to avoid permission issues
COPY src/ /app/src/
COPY migrations/ /app/migrations/
COPY scripts/ /app/scripts/
COPY instance/ /app/instance/
COPY *.py /app/
COPY *.ini /app/

# Create shared module directories (will be mounted as volumes in docker-compose)
RUN mkdir -p /app/shared/middleware /app/shared/utils /app/shared/models /app/shared/schemas

# Create entrypoint script with explicit Unix line endings
RUN echo '#!/bin/bash\n\
\n\
# Wait for database\n\
echo "Waiting for auth-db..."\n\
until PGPASSWORD=$AUTH_DB_PASSWORD psql -h auth-db -U $AUTH_DB_USER -d $AUTH_DB_NAME -c "\q"; do\n\
  >&2 echo "Postgres is unavailable - sleeping"\n\
  sleep 1\n\
done\n\
\n\
>&2 echo "Postgres is up - executing command"\n\
\n\
# Print directory structure for debugging\n\
echo "Directory structure in /app:"\n\
ls -la /app\n\
echo "Directory structure in /app/src:"\n\
ls -la /app/src\n\
echo "Directory structure in /app/shared:"\n\
ls -la /app/shared\n\
\n\
# Check if shared modules are properly mounted\n\
if [ ! -f "/app/shared/database.py" ]; then\n\
    echo "WARNING: Shared modules not properly mounted. Volume mount issue possible."\n\
fi\n\
\n\
# Set Python path\n\
export PYTHONPATH=/app:/app/shared:$PYTHONPATH\n\
\n\
# Initialize migrations if they dont exist\n\
if [ ! -f migrations/alembic.ini ]; then\n\
    flask db init\n\
fi\n\
\n\
# Run migrations\n\
flask db upgrade || echo "Warning: Migrations failed, but continuing..."\n\
\n\
# Start the application\n\
exec gunicorn --bind 0.0.0.0:5001 --workers 2 --threads 4 --timeout 120 "src.app:create_app()"\n\
' > /entrypoint.sh

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Set environment variables
ENV FLASK_APP=src.app
ENV FLASK_DEBUG=0
ENV PYTHONPATH=/app:/app/shared

# Health check with increased timeout
HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:5001/health || exit 1

# Expose port
EXPOSE 5001

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"] 