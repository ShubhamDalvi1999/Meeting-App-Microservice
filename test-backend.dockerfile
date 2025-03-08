FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/flask-service/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app:/app/shared
ENV FLASK_APP=src.app
ENV FLASK_DEBUG=1

CMD ["python", "-c", "import sys; print(sys.path); from flask import Flask; print('Flask version:', Flask.__version__); import flask_wtf; print('Flask-WTF version:', flask_wtf.__version__)"] 