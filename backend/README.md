# Coco-Ai バックエンド

このディレクトリには、Coco-Ai プロジェクトのバックエンドサービスのソースコードが含まれています。Python、FastAPI、および Google Agents Development Kit (ADK) を用いて構築されています。このサービスは Google Cloud Run 上でコンテナとして動作し、Cloud Storage へのファイルアップロードを Eventarc 経由でトリガーされます。

## ✨ アーキテクチャ

バックエンドは、ADK を使用したエージェントベースのワークフローを実装しており、ユーザーが話した質問を処理し、子供向けの解説、イラスト、およびナレーション付きの音声応答を生成します。

### エージェントパイプライン

中心的なロジックは、複数の専門エージェントを順次または並行して実行するパイプラインです。

1.  **`TranscriberAgent`**: Google Cloud Speech-to-Text API を使用して、Cloud Storage にあるユーザーの音声ファイルをテキストに書き起こします。
2.  **`ExplainerAgent`**: 大規模言語モデル（Gemini）を利用し、書き起こされたテキストから以下の情報を構造化された JSON 形式で生成します。
    - 子供向けの簡単な解説文
    - テキスト読み上げ（TTS）用の SSML 形式のテキスト
    - 親子間の会話を促すための親向けのヒント
    - 画像生成用の詳細なプロンプト
3.  **`ParallelAgent` (`IllustrateAndNarrate`)**: 処理時間を短縮するため、2 つのエージェントを並行して実行します。
    - **`IllustratorAgent`**: `ExplainerAgent`からのプロンプトに基づいて Imagen を使用して画像を生成し、Cloud Storage に保存します。
    - **`NarratorAgent`**: Google Cloud Text-to-Speech API を使用して SSML 形式の解説から音声を合成し、Cloud Storage に保存します。
4.  **`ResultWriterAgent`**: パイプラインの最後のエージェントです。先行するすべてのエージェントからの結果（書き起こし、解説、画像 URL、音声 URL）を収集し、最終的なジョブデータを Firestore ドキュメントに書き込みます。また、ワークフロー中のエラーも検知し、ステータスを更新します。

### リアルタイムなステータス更新

`callback.py` に定義されたコールバック関数 (`before_agent_callback`, `after_agent_callback`) を利用し、各エージェントの実行前後に Firestore のジョブステータスを更新します。これにより、フロントエンドは処理の進捗をリアルタイムで追跡できます。

### トリガーの仕組み

- ワークフローは、特定の Cloud Storage バケットへのファイルアップロードを監視する **Eventarc** トリガーによって開始されます。
- Eventarc は、Cloud Run サービスの`/invoke`エンドポイントに**CloudEvent**を送信します。
- `main.py` の FastAPI アプリケーションがこのイベントを解析し、ファイルの GCS URI とジョブのメタデータを抽出してパイプラインを実行します。

## 🚀 開発ガイド

### 前提条件

- Python (3.13)
- uv (高速な Python パッケージインストーラ)
- Google Cloud SDK (プロジェクトに対して認証済みであること)

### セットアップ

1.  **バックエンドディレクトリに移動:**

    ```bash
    cd backend
    ```

2.  **仮想環境の作成と有効化:**

    ```bash
    # 仮想環境を作成
    uv venv

    # 環境を有効化
    # Windows (Git Bash): source .venv/Scripts/activate
    # macOS / Linux:      source .venv/bin/activate
    ```

3.  **依存関係のインストール:**
    プロジェクトの依存関係は `pyproject.toml` と `uv.lock` で管理されています。`uv sync` を使うと、ロックファイルに基づいて依存関係を正確に再現できるため、開発者全員が同じ環境で作業できます。

    ```bash
    # uv.lock ファイルに基づいて、通常と開発用の両方の依存関係を同期します
    uv sync --all-extras

    # 現在のプロジェクトを編集可能モードでインストールします
    # これにより、ソースコードの変更が即座に反映されるようになります
    uv pip install --no-deps -e .
    ```

4.  **環境変数の設定 (プロジェクトルート):**
    サーバーサイドの環境変数は、プロジェクトのルートディレクトリにある単一の `.env` ファイルで管理します。
    まず、**プロジェクトのルートディレクトリ (`coco-ai/`)** に移動し、`.env.example` をコピーして `.env` ファイルを作成してください。

    ```bash
    # In the project root directory (coco-ai/)
    cp .env.example .env
    ```

    | 変数名                    | 説明                                                        |
    | :------------------------ | :---------------------------------------------------------- |
    | `GOOGLE_CLOUD_PROJECT_ID` | あなたの Google Cloud プロジェクト ID。                     |
    | `AUDIO_UPLOAD_BUCKET`     | フロントエンドから音声がアップロードされる GCS バケット名。 |
    | `PROCESSED_AUDIO_BUCKET`  | 生成された解説音声（MP3）を保存する GCS バケット名。        |
    | `GENERATED_IMAGE_BUCKET`  | 生成されたイラスト（PNG）を保存する GCS バケット名。        |

### ローカルでの実行

開発とテストのために、FastAPI サーバーをローカルで実行できます。`--reload` フラグにより、コード変更時にサーバーが自動的にリロードされます。

```bash
uvicorn main:app --reload
```

`/invoke` エンドポイントをテストするには、Eventarc の CloudEvent をシミュレートする必要があります。`curl` や Postman などのツールを使い、`StorageObjectData` モデルを模した有効な JSON ペイロードを持つ POST リクエストを送信します。

## デプロイ

このサービスは、コンテナとして Google Cloud Run にデプロイされるように設計されています。

1.  **Docker コンテナのビルド:**

    ```bash
    gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/coco-ai-backend
    ```

    `YOUR_PROJECT_ID` を実際の Google Cloud プロジェクト ID に置き換えてください。

2.  **Cloud Run へのデプロイ:**
    ```bash
    gcloud run deploy coco-ai-backend \
      --image gcr.io/YOUR_PROJECT_ID/coco-ai-backend \
      --platform managed \
      --region YOUR_REGION \
      --env-file .env
    ```
    - `YOUR_PROJECT_ID` と `YOUR_REGION`　を実際の値に置き換えてください。.
    - **セキュリティに関する注意**: 上記のコマンド例には含まれていませんが、本番環境では `--allow-unauthenticated` フラグを使用せず、認証を有効にすることを強く推奨します。Eventarc トリガーに Cloud Run サービスを呼び出す権限 (`roles/run.invoker`) を持つサービスアカウントを関連付けることで、セキュアな呼び出しが可能です。
    - デプロイする前に、`.env` ファイルが正しく設定されていることを確認してください。

デプロイ後、指定された Cloud Storage バケットにファイルがアップロードされたときにこのサービスを呼び出すように Eventarc トリガーを設定します。
