# Multi-stage build using openenv-base
# Works for both in-repo and standalone deployment to Hugging Face Spaces.

ARG BASE_IMAGE=ghcr.io/meta-pytorch/openenv-base:latest
FROM ${BASE_IMAGE} AS builder

WORKDIR /app

ARG BUILD_MODE=standalone

# Copy environment code
COPY . /app/env

WORKDIR /app/env

# Ensure uv is available
RUN if ! command -v uv > /dev/null 2>&1; then \
        curl -LsSf https://astral.sh/uv/install.sh | sh && \
        mv /root/.local/bin/uv /usr/local/bin/uv && \
        mv /root/.local/bin/uvx /usr/local/bin/uvx; \
    fi

# Install git (needed for some openenv-core builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (two-pass for better layer caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r server/requirements.txt --system

# ----- Runtime stage -----
FROM ${BASE_IMAGE}

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy environment code
COPY --from=builder /app/env /app/env

ENV PYTHONPATH="/app/env:$PYTHONPATH"

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the FastAPI server
CMD ["sh", "-c", "cd /app/env && uvicorn server.app:app --host 0.0.0.0 --port 8000"]
