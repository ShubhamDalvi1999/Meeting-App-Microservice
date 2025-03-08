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
    pip list | grep Flask && pip list | grep gunicorn

# Create necessary directories
RUN mkdir -p /app/migrations/versions /app/logs /app/src /app/scripts /app/instance

# Copy files by directory to avoid permission issues
COPY src/ /app/src/
COPY migrations/ /app/migrations/
COPY scripts/ /app/scripts/
COPY instance/ /app/instance/
COPY *.py /app/
COPY *.ini /app/

# Set environment variables
ENV FLASK_APP=src.app
ENV FLASK_DEBUG=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5001

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Wait for database\n\
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
echo "Directory structure in /app/migrations:"\n\
ls -la /app/migrations\n\
\n\
# Set Python path\n\
export PYTHONPATH=/app\n\
\n\
# Initialize migrations if they dont exist\n\
if [ ! -f migrations/alembic.ini ]; then\n\
    flask db init\n\
fi\n\
\n\
# Run migrations\n\
flask db upgrade\n\
\n\
# Start the application\n\
exec gunicorn --bind 0.0.0.0:5001 --workers 4 --threads 8 --timeout 0 "src.app:create_app()"' > /entrypoint.sh && \
chmod +x /entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:5001/health || exit 1

# Run the entrypoint script
CMD ["/entrypoint.sh"] 