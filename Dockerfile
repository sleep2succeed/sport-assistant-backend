# Multi-stage build using uv for fast, reproducible Python installs.

# --- Stage 1: install deps with uv ---
FROM python:3.12-slim AS build

# Install uv (fast Python package manager).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy only manifests first so Docker caches the install layer.
COPY pyproject.toml uv.lock* ./

# Create a virtualenv at /app/.venv with locked deps.
# `--frozen` requires uv.lock to be up to date; drop it if you haven't run `uv lock` yet.
RUN uv sync --no-install-project --no-dev || uv sync --no-install-project

# --- Stage 2: runtime ---
FROM python:3.12-slim

WORKDIR /app

# Copy the venv from the build stage.
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code.
COPY src ./src

# The app imports as `src` — main.py does `from src.routers import ...`.
# Make `src` importable as `backend` by exposing it on PYTHONPATH via a symlink.
RUN ln -s /app/src /app/backend

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
