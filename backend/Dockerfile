# syntax=docker/dockerfile:1
# Build version: 2026-03-03-BGE-large-v1
# Upgrade: BGE-small (384d) → BGE-large (1024d) for higher accuracy

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

# Install BM25 for hybrid search
RUN pip install --no-cache-dir rank-bm25

COPY pyproject.toml poetry.lock ./
# Regenerate lock file if pyproject.toml changed, then install
RUN poetry lock && poetry install --only main --no-root --no-ansi

# ============ Runtime Stage ============
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    # PyTorch CPU optimizations - increased for BGE-large (1024d)
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    EMBEDDING_CPU_THREADS=4 \
    # Disable tokenizers parallelism to avoid deadlocks in containers
    TOKENIZERS_PARALLELISM=false \
    # Transformers cache directory (for RoBERTa model)
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface \
    # Sentence transformers cache (for BGE embeddings)
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

WORKDIR /app

# Create cache directories for model storage
RUN mkdir -p /app/.cache/huggingface /app/.cache/sentence-transformers

# Copy only the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

COPY app ./app

# Pre-download models during build to avoid startup timeout
RUN python -c "from transformers import AutoModelForSequenceClassification, AutoTokenizer; \
    AutoModelForSequenceClassification.from_pretrained('cardiffnlp/twitter-roberta-base-sentiment-latest'); \
    AutoTokenizer.from_pretrained('cardiffnlp/twitter-roberta-base-sentiment-latest')" && \
    python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('BAAI/bge-large-en-v1.5')"

# Hugging Face Spaces uses port 7860 by default
EXPOSE 7860

# Add a non-root user for security on Hugging Face
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy files with correct ownership
COPY --chown=user . .
COPY --from=builder --chown=user /app/.venv /home/user/app/.venv

# Health check for Hugging Face - increased timeout for BGE-large (1024d model)
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD python -c "import os, urllib.request; port = os.getenv('PORT', '7860'); urllib.request.urlopen(f'http://localhost:{port}/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:create_app --factory --host 0.0.0.0 --port 7860"]
