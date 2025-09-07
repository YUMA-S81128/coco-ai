# -----------------------------
# Builder stage
# -----------------------------
FROM python:3.13.7-slim-trixie AS builder
ARG UV_VERSION=0.8.13
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Build deps only in builder
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc libffi-dev libssl-dev git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存定義（ロックファイル）を先にコピーしてレイヤーを固定
COPY pyproject.toml uv.lock ./

# uv CLI をシステム側に入れる
RUN python -m pip install --no-cache-dir "uv==${UV_VERSION}"

# UV_PROJECT_ENVIRONMENT / VIRTUAL_ENV を設定済みなので
# uv venv と uv sync が /opt/venv を使ってインストール
# --frozen で lockfile 準拠、--no-dev で dev deps を省く
RUN uv venv ${VIRTUAL_ENV} \
 && uv sync --frozen --no-dev

# ソースをコピー
COPY . .

# アプリ本体を venv にインストール（editable）。依存は既に同期済みなので --no-deps を指定
RUN uv pip install --no-cache-dir --no-deps -e .

# -----------------------------
# Final stage
# -----------------------------
FROM python:3.13.7-slim-trixie AS final
ENV PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PORT=8080 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# 最小限のランタイム依存のみ
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# 非 root ユーザー作成
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup appuser

WORKDIR ${APP_HOME}

# builder から venv を丸ごとコピー
COPY --from=builder /opt/venv /opt/venv

# アプリコードはコンテナ内にコピー（--chown で所有権付与）
# .dockerignore を用意して余計なファイルを含めないこと
COPY --chown=appuser:appgroup . .

# venv とアプリの所有権を最終的に調整してから非 root に切り替え
RUN chown -R appuser:appgroup /opt/venv ${APP_HOME}

USER appuser

# 起動（exec を使ってシグナルを正しく伝搬）
ENTRYPOINT ["sh", "-c", "exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers"]
