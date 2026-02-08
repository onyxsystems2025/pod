FROM python:3.12-slim

# System dependencies for weasyprint and psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libglib2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements/base.txt requirements/base.txt
COPY requirements/prod.txt requirements/prod.txt
RUN pip install --no-cache-dir -r requirements/prod.txt

# Copy project
COPY . .

# Collect static files
RUN DJANGO_SETTINGS_MODULE=config.settings.prod \
    SECRET_KEY=build-placeholder \
    DB_HOST=placeholder \
    python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
