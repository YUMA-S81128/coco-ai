# Coco-Ai Cloud Functions for Firebase

> Google Cloud Japan AI Hackathon vol.3 応募作品

このディレクトリは、親子対話AI「Coco-Ai」プロジェクトで使用される **Cloud Functions for Firebase** のソースコードを格納します。

## 役割

このFunctionは、フロントエンドとバックエンド処理を安全かつ非同期に連携させるための「受付窓口」として、**HTTPS Callable Function** （アプリから直接呼び出せるタイプの関数）として実装されています。

フロントエンドアプリから直接呼び出されることで、**署名付きURL**と**ジョブID**を発行します。

1.  **ジョブIDの生成**: これから始まるAI処理全体を識別するための一意なID（例: `job-12345`）を生成します。
2.  **署名付きURLの発行**: フロントエンドが認証情報なしで、かつ安全にCloud Storageへ音声ファイルを直接アップロードするための一時的なURLを発行します。このURLには、後続の処理で必要となるジョブIDがカスタムメタデータとして含まれます。
3.  **Firestoreへのジョブ登録**: 生成したジョブIDでFirestoreにドキュメントを作成し、処理のステータス管理を開始します。

## API仕様

### レスポンス

このFunctionは、呼び出し元のフロントエンドに対して以下の形式のJSONを返却します。

```json
{
  "jobId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "uploadUrl": "https://storage.googleapis.com/..."
}
```

この仕組みにより、フロントエンドは重い音声ファイルを直接サーバーに送信することなく、安全なアップロードとリアルタイムな進捗確認を実現できます。

## 連携フローにおける位置付け

1.  **フロントエンド → Cloud Functions (HTTPS Callable)**: このディレクトリで管理するFunctionです。
2.  フロントエンド → Cloud Storage: 発行された署名付きURLを使ってアップロードします。
3.  Cloud Storage → **Eventarc** → Cloud Run: ファイルのアップロードをトリガーにAI処理が実行されます。

## 開発フロー

### 1. 前提条件

-   [Python](https://www.python.org/downloads/) (3.12以上) がインストールされていること。
-   [uv](https://github.com/astral-sh/uv) (高速なPythonパッケージインストーラ) がインストールされていること。
-   [Firebase CLI](https://firebase.google.com/docs/cli) がインストール・設定されていること。

### 2. 依存関係のインストール

このFunctionはPythonで記述されています。依存関係は `requirements.txt` で管理され、仮想環境は `uv` を使って構築します。

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

Firebase Emulator Suite を使うことで、このFunctionをローカルでテストできます。プロジェクトのルートディレクトリで以下のコマンドを実行してください。フロントエンドアプリからの呼び出しに応じて、このFunctionがローカルで実行されます。

```bash
firebase emulators:start
```

### 4. デプロイ

このFunctionをデプロイするには、プロジェクトのルートディレクトリで以下のコマンドを実行します。

```bash
firebase deploy --only functions
```

1.  **フロントエンド → Cloud Functions (HTTPS Callable)**: このディレクトリで管理するFunctionです。
2.  フロントエンド → Cloud Storage: 発行された署名付きURLを使ってアップロードします。
3.  Cloud Storage → **Eventarc** → Cloud Run: ファイルのアップロードをトリガーにAI処理が実行されます。

## ⚙️ 設定

このFunctionを正しく動作させるためには、環境変数の設定が必要です。

-   `AUDIO_UPLOAD_BUCKET`: フロントエンドからアップロードされる音声ファイルを保存するCloud Storageのバケット名。