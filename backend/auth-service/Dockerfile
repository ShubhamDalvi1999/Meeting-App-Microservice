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

# Create migrations directory structure
RUN mkdir -p migrations/versions

# Copy migration file
COPY migrations/versions/001_initial.py migrations/versions/

# Create alembic.ini
RUN echo '[alembic]\n\
script_location = migrations\n\
sqlalchemy.url = driver://user:pass@localhost/dbname\n\
\n\
[loggers]\n\
keys = root,sqlalchemy,alembic\n\
\n\
[handlers]\n\
keys = console\n\
\n\
[formatters]\n\
keys = generic\n\
\n\
[logger_root]\n\
level = WARN\n\
handlers = console\n\
qualname =\n\
\n\
[logger_sqlalchemy]\n\
level = WARN\n\
handlers =\n\
qualname = sqlalchemy.engine\n\
\n\
[logger_alembic]\n\
level = INFO\n\
handlers =\n\
qualname = alembic\n\
\n\
[handler_console]\n\
class = StreamHandler\n\
args = (sys.stderr,)\n\
level = NOTSET\n\
formatter = generic\n\
\n\
[formatter_generic]\n\
format = %(levelname)-5.5s [%(name)s] %(message)s\n\
datefmt = %H:%M:%S\n' > alembic.ini

# Create migrations/env.py
RUN echo 'from logging.config import fileConfig\n\
\n\
from sqlalchemy import engine_from_config\n\
from sqlalchemy import pool\n\
\n\
from alembic import context\n\
from src.app import create_app\n\
from src.database import db\n\
\n\
config = context.config\n\
\n\
if config.config_file_name is not None:\n\
    fileConfig(config.config_file_name)\n\
\n\
app = create_app()\n\
target_metadata = db.metadata\n\
\n\
def run_migrations_offline() -> None:\n\
    url = app.config["SQLALCHEMY_DATABASE_URI"]\n\
    context.configure(\n\
        url=url,\n\
        target_metadata=target_metadata,\n\
        literal_binds=True,\n\
        dialect_opts={"paramstyle": "named"},\n\
    )\n\
\n\
    with context.begin_transaction():\n\
        context.run_migrations()\n\
\n\
def run_migrations_online() -> None:\n\
    configuration = config.get_section(config.config_ini_section)\n\
    configuration["sqlalchemy.url"] = app.config["SQLALCHEMY_DATABASE_URI"]\n\
    connectable = engine_from_config(\n\
        configuration,\n\
        prefix="sqlalchemy.",\n\
        poolclass=pool.NullPool,\n\
    )\n\
\n\
    with connectable.connect() as connection:\n\
        context.configure(\n\
            connection=connection,\n\
            target_metadata=target_metadata\n\
        )\n\
\n\
        with context.begin_transaction():\n\
            context.run_migrations()\n\
\n\
if context.is_offline_mode():\n\
    run_migrations_offline()\n\
else:\n\
    run_migrations_online()' > migrations/env.py

# Create migrations/README
RUN echo 'Generic single-database configuration.' > migrations/README

# Create migrations/script.py.mako
RUN echo '"""${message}\n\
\n\
Revision ID: ${up_revision}\n\
Revises: ${down_revision | comma,n}\n\
Create Date: ${create_date}\n\
\n\
"""\n\
from alembic import op\n\
import sqlalchemy as sa\n\
${imports if imports else ""}\n\
\n\
# revision identifiers, used by Alembic.\n\
revision = ${repr(up_revision)}\n\
down_revision = ${repr(down_revision)}\n\
branch_labels = ${repr(branch_labels)}\n\
depends_on = ${repr(depends_on)}\n\
\n\
\n\
def upgrade() -> None:\n\
    ${upgrades if upgrades else "pass"}\n\
\n\
\n\
def downgrade() -> None:\n\
    ${downgrades if downgrades else "pass"}' > migrations/script.py.mako

# Create entrypoint script
RUN echo '#!/bin/sh\n\
flask db upgrade && \
gunicorn --bind 0.0.0.0:5001 "src.app:create_app()"' > /entrypoint.sh && \
chmod +x /entrypoint.sh

# Expose port
EXPOSE 5001

# Run migrations and start the application
CMD ["/entrypoint.sh"] 