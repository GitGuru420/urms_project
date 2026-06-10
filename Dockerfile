# Use official slim Python build layer
FROM python:3.11-slim

# System optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for PostgreSQL connectivity compiling
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cache dependency builds
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy complete repository asset base
COPY . /app/

# Compile production-grade compressed manifest static asset files
RUN python manage.py collectstatic --noinput

# Launch runtime processes under optimized user security levels
EXPOSE 8000
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]