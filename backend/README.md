# Coco-Ai バックエンド (Python / Cloud Run / ADK)

> Google Cloud Japan AI Hackathon vol.3 応募作品

このディレクトリは、親子対話 AI「Coco-Ai」のバックエンドアプリケーションです。
Cloud Run 上で動作する Python で構築されており、中核的な AI 処理を担います。

## 役割

このバックエンドは、Cloud Storage へのファイルアップロードを**Eventarc**が検知することをトリガーとして起動され、複雑な AI 処理を実行する「専門家の作業場」です。

- **AI エージェントシステム**: Agents Development Kit (ADK) を用いて、複数の AI エージェントが協調して動作するシステムを構築しています。
- **マルチモーダル処理**: Google Cloud の最新 AI API を活用し、音声・テキスト・画像を統合したリッチな応答を生成します。
  - **Speech-to-Text**: 子供の音声をテキストに変換します。
  - **Gemini API**: テキスト化された質問の意図を理解し、子供向けの解説と親向けのヒントを生成します。
  - **Imagen API**: 解説に合わせたイラストをリアルタイムで生成します。
  - **Text-to-Speech**: 生成された解説文を自然な音声で読み上げます。
- **Firebase 連携**: Eventarc から受け取ったイベント情報（ファイルメタデータに含まれるジョブ ID など）を元に、処理の進捗や結果を Firestore に書き込みます。生成した成果物（画像、音声ファイル）は Cloud Storage に保存します。

## AI エージェント構成

- **受付・通訳エージェント**: 子供のあいまいな発音も正確にテキスト化します。
- **対話・解説エージェント**: 質問の意図を汲み取り、子供の年齢に合わせた回答、イラスト指示、そして親向けヒントを生成する司令塔です。
- **イラストレーターエージェント**: 解説内容を補足する、わかりやすく可愛いイラストをその場で生成します。
- **ナレーターエージェント**: 解説文を優しく温かみのある声で読み上げます。

## 開発フロー

### 1. 前提条件

- [Python](https://www.python.org/downloads/) (3.13 以上) がインストールされていること。
- [uv](https://github.com/astral-sh/uv) (高速な Python パッケージインストーラ) がインストールされていること。

### 2. 依存関係のインストール

このバックエンドは Python で記述されています。依存関係は `pyproject.toml` で管理され、仮想環境は `uv` を使って構築します。

```bash
# backend ディレクトリに移動
cd backend

# 仮想環境を作成
uv venv

# 仮想環境を有効化
#   Windows (Git Bashの場合):
#   source .venv/Scripts/activate
#   Windows (コマンドプロンプトの場合):
#   .\.venv\Scripts\activate
#   macOS / Linux の場合:
#   source .venv/bin/activate

# 依存パッケージをインストール (開発用ツールも含む)
uv sync --all-extras
```

### 3. デプロイ

このバックエンドは、Cloud Run サービスとしてデプロイされます。

1.  **gcloud CLI の認証**: Google Cloud にログインします。
    ```bash
    gcloud auth login
    ```
2.  **Cloud Run へのデプロイ**: `backend` ディレクトリから以下のコマンドを実行します。`[SERVICE_NAME]` は任意のサービス名に、`[REGION]` はデプロイするリージョン（例: `asia-northeast1`）に置き換えてください。
    ```bash
    gcloud run deploy [SERVICE_NAME] --source . --region [REGION] --allow-unauthenticated
    ```

```

```
