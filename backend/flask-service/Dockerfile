FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install APScheduler==3.10.4

# Create necessary directories
RUN mkdir -p /app/shared /app/logs /app/src /app/migrations

# Copy fixed app.py file with explicit import modifications
COPY fixed_app.py /app/src/app.py

# Copy application code by directory to avoid permission issues
COPY src/ /app/src/
COPY migrations/ /app/migrations/
COPY *.py /app/
COPY *.sh /app/

# Copy shared module files 
# Note: In docker-compose, we'll mount these as volumes, but this ensures they exist if volume mount fails
RUN mkdir -p /app/shared/middleware /app/shared/utils /app/shared/models /app/shared/schemas

# Create entrypoint script with explicit Unix line endings
RUN echo '#!/bin/bash\n\
\n\
# Wait for postgres\n\
echo "Waiting for postgres..."\n\
while ! pg_isready -h postgres -p 5432 -U $POSTGRES_USER -d $POSTGRES_DB; do\n\
    echo "Postgres is unavailable - sleeping"\n\
    sleep 1\n\
done\n\
echo "Postgres is up - executing command"\n\
\n\
# Print directory structure for debugging\n\
echo "Directory structure in /app:"\n\
ls -la /app\n\
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
# Run database migrations\n\
echo "Running database migrations..."\n\
cd /app\n\
flask db upgrade || echo "Warning: Migrations failed, but continuing..."\n\
\n\
# Start the application\n\
echo "Starting application..."\n\
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 120 "src.app:create_app()"\n\
' > /entrypoint.sh

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Set environment variables
ENV FLASK_APP=src.app
ENV FLASK_DEBUG=0
ENV PYTHONPATH=/app:/app/shared

# Health check with increased timeout
HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"] 