# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies only if needed by pip packages
RUN apt-get update && apt-get install --yes --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

ENV FRIENDLY_PARAKEET_HOST=0.0.0.0
ENV FRIENDLY_PARAKEET_PORT=8000

CMD ["friendly-parakeet-web"]
