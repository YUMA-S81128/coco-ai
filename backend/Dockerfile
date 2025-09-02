# ベースイメージとしてPython 3.13の軽量版を使用
FROM python:3.13-slim

# 環境変数: Pythonの出力をバッファリングしないように設定
ENV PYTHONUNBUFFERED 1

# 作業ディレクトリを設定
WORKDIR /app

# 高速なPythonパッケージインストーラ `uv` をインストール
RUN pip install uv

# 依存関係ファイルをコピー
COPY pyproject.toml ./

# `uv` を使って本番用の依存関係をインストール
# --system: 仮想環境を作成せず、システムのPythonに直接インストール
# --no-cache: キャッシュを使わず、イメージサイズを削減
RUN uv pip install --system --no-cache .

# アプリケーションコードをコピー
COPY . .

# Cloud Runが提供するPORT環境変数でuvicornを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
