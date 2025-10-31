# ================================
# Builder Stage
# ================================
FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

# prevent Python bytecode and buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# install system deps needed to build native extensions (psycopg, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# install uv (https://docs.astral.sh/uv/)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# ensure uv is on PATH
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# copy dependency files
COPY pyproject.toml uv.lock ./

# install dependencies into .venv using uv
RUN --mount=type=cache,id=cache-uv,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# copy application code
COPY src/ ./src/
COPY alembic.ini ./

# ================================
# Runtime Stage
# ================================
FROM python:3.13-slim-bookworm

# install runtime dependencies AS ROOT (before switching user)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# create non-root user
RUN useradd --create-home --shell /bin/bash sasabot
USER sasabot
WORKDIR /home/sasabot/app

# set environment
ENV PATH="/home/sasabot/app/.venv/bin:$PATH" \
    PYTHONPATH="/home/sasabot/app/src"

# copy from builder
COPY --from=builder --chown=sasabot:sasabot /app /home/sasabot/app

# expose port
EXPOSE 7000

# run with uvicorn (production-ready)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7000", "--workers", "2"]