# ---------------------------------------- BUILDER -------------------------
FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

# prevent Python bytecode and buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# install system dependencies (needed for psycopg2, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# install uv (https://docs.astral.sh/uv/)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# ensure uv is on PATH (uv installs under ~/.local/bin by default)
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# copy dependency definitions
COPY pyproject.toml uv.lock ./

# install production dependencies into .venv (no dev, no project install)
RUN uv sync --frozen --no-install-project --no-dev --no-editable

# sanity check
RUN ls -l .venv/bin && .venv/bin/uvicorn --version || echo "uvicorn missing!"

# copy application source
COPY src/ ./src/
COPY alembic.ini ./


# ---------------------------------------- RUNTIME -------------------------
FROM python:3.13-slim-bookworm

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# create non-root user for security
RUN useradd --create-home --shell /bin/bash sasabot
USER sasabot
WORKDIR /home/sasabot/app

# environment setup for runtime
ENV PATH="/home/sasabot/app/.venv/bin:$PATH" \
    PYTHONPATH="/home/sasabot/app/src"

# copy from builder (including .venv)
COPY --from=builder --chown=sasabot:sasabot /app /home/sasabot/app

# expose app port
EXPOSE 7000

# run with uvicorn in production mode
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7000", "--workers", "2"]