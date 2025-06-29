# syntax=docker/dockerfile:1.4
FROM python:3.12-slim

# ML/AI依存に必要な最小限のシステム依存
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
        curl \
        ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --compile-bytecode --no-dev

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace
ENV HF_ENDPOINT=https://hf-mirror.com

# mount

# アプリケーションコードをコピー
COPY ./src ./src
COPY ./config.yaml .

# 仮想環境をアクティベート
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 10000

# 本番用（reloadなし）
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "10000"]