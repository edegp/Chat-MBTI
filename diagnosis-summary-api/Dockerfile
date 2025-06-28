FROM python:3.12-slim AS builder

# 開発ツールは “一時的” にのみ入れる
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- 依存ファイルだけ先にコピー（レイヤキャッシュ最大化） ----
COPY pyproject.toml uv.lock ./

# ---- uv で仮想環境を構築。wheel キャッシュは BuildKit に退避 ----
ENV UV_LINK_MODE=copy
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode --no-dev

########################
# 2) runtime – 軽量化
########################
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*
# ---------- 基本実行環境 ----------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1           \
    HF_HOME=/workspace/.cache/huggingface \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# builder から “出来上がった venv” だけコピー（10 MB 台）
COPY --from=builder /app/.venv /app/.venv

# アプリ本体
COPY src ./src
COPY config.yaml .

EXPOSE 10000
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "10000"]