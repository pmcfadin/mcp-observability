# syntax=docker/dockerfile:1.4

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies via Poetry export -> requirements.txt to keep final image small
COPY pyproject.toml .

RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry export -f requirements.txt --without-hashes | pip install --no-cache-dir -r /dev/stdin \
    && pip uninstall -y poetry

# Copy application code
COPY app app

# Copy runtime entrypoint
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose server port
EXPOSE 8000

# Default command relies on entrypoint script which handles TLS flags
ENTRYPOINT ["/entrypoint.sh"] 