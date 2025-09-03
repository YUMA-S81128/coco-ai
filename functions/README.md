# Coco-Ai Cloud Functions for Firebase

このディレクトリは、「Coco-Ai」プロジェクトで使用される **Cloud Functions for Firebase** のソースコードを格納します。

## Role

この Function は、フロントエンドアプリケーションとバックエンドの処理パイプラインを接続する、安全な「受付窓口」として機能します。クライアントアプリから直接呼び出すことができる **HTTPS Callable Function** として実装されています。

主な責務は、フロントエンドからのリクエストに応じて **署名付き URL (Signed URL)** と **ジョブ ID (Job ID)** を発行することです。

1.  **ジョブ ID の生成**: これから開始される AI 処理ワークフロー全体を識別するための一意な ID（例: `job-12345`）を作成します。
2.  **署名付き URL の発行**: クライアントがサービスアカウントの認証情報なしで、音声ファイルを Cloud Storage に直接アップロードできる、一時的で安全な URL を生成します。この URL は、アップロードリクエストにカスタムメタデータ（`jobId`と`userId`）を含めることを要求するように設定されています。
3.  **Firestore へのジョブ登録**: 生成された`jobId`を使用して Firestore に新しいドキュメントを作成し、ジョブのステータス追跡を開始します。

## API 仕様

### Response

この関数は、呼び出し元のクライアントに以下の形式で JSON オブジェクトを返します。

```json
{
  "jobId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "signedUrl": "https://storage.googleapis.com/..."
}
```

この仕組みにより、フロントエンドは重い音声ファイルを直接サーバーに送信することなく、安全なアップロードとリアルタイムな進捗確認を実現できます。

## 連携フローにおける位置付け

1.  **フロントエンド → Cloud Functions (HTTPS Callable)**: このディレクトリで管理する Function です。
2.  フロントエンド → Cloud Storage: 発行された署名付き URL を使ってアップロードします。
3.  Cloud Storage → **Eventarc** → Cloud Run: ファイルのアップロードをトリガーに AI 処理が実行されます。

## 開発フロー

### 1. 前提条件

- [Python](https://www.python.org/downloads/) (3.12 以上) がインストールされていること。
- [uv](https://github.com/astral-sh/uv) (高速な Python パッケージインストーラ) がインストールされていること。
- [Firebase CLI](https://firebase.google.com/docs/cli) がインストール・設定されていること。

### 2. 依存関係のインストール

この Function は Python で記述されています。依存関係は `requirements.txt` で管理され、仮想環境は `uv` を使って構築します。

```bash
# functions ディレクトリに移動
cd functions

# 仮想環境を作成
uv venv

# 仮想環境を有効化
#   Windows (Git Bashの場合):
#   source .venv/Scripts/activate
#   Windows (コマンドプロンプトの場合):
#   .\.venv\Scripts\activate
#   macOS / Linux の場合:
#   source .venv/bin/activate

# 依存パッケージをインストール
uv pip install -r requirements.txt
```

### 3. ローカルでの動作確認

Firebase Emulator Suite を使うことで、この Function をローカルでテストできます。プロジェクトのルートディレクトリで以下のコマンドを実行してください。

```bash
firebase emulators:start
```

エミュレータを起動後、`app`ディレクトリの`README.md`に従って Flutter アプリを起動すると、アプリからのリクエストに応じてこの Function がローカルで実行されます。

> **Note:** 起動したエミュレータを停止するには、エミュレータが実行されているターミナルで `Ctrl + C` を押します。

### 4. デプロイ

この Function をデプロイするには、プロジェクトのルートディレクトリで以下のコマンドを実行します。

```bash
firebase deploy --only functions
```

## ⚙️ 設定

この Function は `pydantic-settings` を利用して、プロジェクトのルートディレクトリにある `.env` ファイルから環境変数を読み込みます。

1.  **プロジェクトのルートディレクトリ (`coco-ai/`)** に移動し、`.env.example` ファイルをコピーして `.env` ファイルを作成します。
    ```bash
    # In the project root directory (coco-ai/)
    cp .env.example .env
    ```
2.  作成した `.env` ファイルを編集し、お使いの環境に合わせて値を設定します。
    - `AUDIO_UPLOAD_BUCKET`: フロントエンドからアップロードされる音声ファイルを保存する Cloud Storage のバケット名。

### デプロイ時の環境変数

Firebase Functions にデプロイする際は、`.env` ファイルの内容をランタイムの環境変数として設定する必要があります。`firebase deploy` コマンドに `--set-env-vars` フラグを追加するか、Google Cloud Secret Manager を利用して設定してください。

**例:** `firebase deploy --only functions --set-env-vars AUDIO_UPLOAD_BUCKET=your-bucket-name`
