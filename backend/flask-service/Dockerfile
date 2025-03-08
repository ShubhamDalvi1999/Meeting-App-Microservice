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

# Install Python dependencies with pip upgrade
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create a proper directory structure
RUN mkdir -p /app/shared /app/logs

# Copy service code and shared code separately
COPY . /app/
# This will be mounted in docker-compose

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=src.app
ENV FLASK_DEBUG=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Create entrypoint script
RUN echo '#!/bin/sh\n\
echo "Waiting for postgres..."\n\
while ! pg_isready -h postgres -p 5432 -U $POSTGRES_USER -d $POSTGRES_DB; do\n\
    echo "Postgres is unavailable - sleeping"\n\
    sleep 1\n\
done\n\
echo "Postgres is up - executing command"\n\
\n\
# Print directory structure for debugging\n\
echo "Directory structure:"\n\
ls -la /app\n\
echo "Shared directory:"\n\
ls -la /app/shared\n\
\n\
# Run migrations\n\
flask db upgrade\n\
\n\
# Start application\n\
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 8 --timeout 0 "src.app:create_app()"' > /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Start the application
CMD ["/entrypoint.sh"] 