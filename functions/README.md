# Coco-Ai Cloud Functions for Firebase

> Google Cloud Japan AI Hackathon vol.3 応募作品

このディレクトリは、親子対話 AI「Coco-Ai」プロジェクトで使用される **Cloud Functions for Firebase** のソースコードを格納します。

## 役割

この Function は、フロントエンドとバックエンド処理を安全かつ非同期に連携させるための「受付窓口」として、**HTTPS Callable Function** （アプリから直接呼び出せるタイプの関数）として実装されています。

フロントエンドアプリから直接呼び出されることで、**署名付き URL**と**ジョブ ID**を発行します。

1.  **ジョブ ID の生成**: これから始まる AI 処理全体を識別するための一意な ID（例: `job-12345`）を生成します。
2.  **署名付き URL の発行**: フロントエンドが認証情報なしで、かつ安全に Cloud Storage へ音声ファイルを直接アップロードするための一時的な URL を発行します。この URL には、後続の処理で必要となるジョブ ID がカスタムメタデータとして含まれます。
3.  **Firestore へのジョブ登録**: 生成したジョブ ID で Firestore にドキュメントを作成し、処理のステータス管理を開始します。

## API 仕様

### レスポンス

この Function は、呼び出し元のフロントエンドに対して以下の形式の JSON を返却します。

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

この Function を正しく動作させるためには、環境変数の設定が必要です。

- `AUDIO_UPLOAD_BUCKET`: フロントエンドからアップロードされる音声ファイルを保存する Cloud Storage のバケット名。
