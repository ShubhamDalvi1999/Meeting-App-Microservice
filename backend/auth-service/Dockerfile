FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=src/app.py
ENV PYTHONPATH=/app

# Create entrypoint script
RUN echo '#!/bin/sh\n\
python -c "from src.app import init_db; init_db()" && \
gunicorn --bind 0.0.0.0:5001 "src.app:create_app()"' > /entrypoint.sh && \
chmod +x /entrypoint.sh

# Expose port
EXPOSE 5001

# Run migrations and start the application
CMD ["/entrypoint.sh"] 