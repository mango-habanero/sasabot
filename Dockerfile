# base python image
FROM python:3.13-slim-bookworm

# set working directory
WORKDIR /app

# environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq5 \
    libpq-dev \
    python3-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# install uv (modern python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# copy dependency files
COPY pyproject.toml uv.lock ./

# install only production dependencies (no dev, no editable)
RUN uv sync --frozen --no-install-project --no-dev --no-editable

# copy application source
COPY src/ ./src/
COPY alembic.ini ./

# expose port
EXPOSE 7000

# run app with uvicorn inside the uv environment
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7000", "--workers", "2"]
