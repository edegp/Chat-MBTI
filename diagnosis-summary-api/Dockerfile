# ---------- deps ステージ（依存インストール専用）----------
FROM python:3.12-slim AS deps
# uv バイナリを先にコピー
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# システム依存のみインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存情報だけをコピー（ここがキャッシュ境界！）
COPY pyproject.toml uv.lock ./

ENV UV_LINK_MODE=copy
# BuildKit + キャッシュマウントを使うとさらに速い
RUN uv venv /tmp
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --compile-bytecode --no-editable

# ---------- runtime ステージ（実行用）----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
# バッファの無効化
ENV PYTHONUNBUFFERED 1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


WORKDIR /app
# 依存ライブラリだけをコピー
# システム依存はインストールしない
COPY --from=deps /tmp /tmp
RUN uv venv /tmp

# アプリソースを最後にコピー
COPY . .

# （開発用なら reload で OK、商用なら外す）
EXPOSE 10000

CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "10000"]
