# Dockerfile for BigQuery HTTP Server (ChatGPT Integration)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS uv

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy pyproject.toml and lock file for dependencies
COPY pyproject.toml uv.lock ./

# Install the project's dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Add the rest of the project source code and install it
ADD src /app/src

# Sync and install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Copy virtual environment from the builder
COPY --from=uv /root/.local /root/.local
COPY --from=uv --chown=app:app /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Expose HTTP port
EXPOSE 8000

# Define the entry point for HTTP server
ENTRYPOINT ["mcp-server-bigquery-http"]

# Default command runs on all interfaces
CMD []