# syntax=docker/dockerfile:1

# ============ Builder Stage ============
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.2.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-ansi

# ============ Runtime Stage ============
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    # PyTorch CPU optimizations
    OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2 \
    EMBEDDING_CPU_THREADS=2 \
    # Disable tokenizers parallelism to avoid deadlocks in containers
    TOKENIZERS_PARALLELISM=false \
    # Transformers cache directory (for RoBERTa model)
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface \
    # Sentence transformers cache (for MiniLM embeddings)
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

WORKDIR /app

# Create cache directories for model storage
RUN mkdir -p /app/.cache/huggingface /app/.cache/sentence-transformers

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

COPY app ./app

EXPOSE 8000

# Health check for Railway/container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
