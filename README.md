# 親子対話 AI「Coco-Ai」

> Google Cloud Japan AI Hackathon vol.3 応募作品

> 子供の「なんで？」が、親子の最高の学びに変わる

Coco-Ai は、子供の尽きない好奇心に対し、2 人のキャラクター「ココ」と「アイ」が対話とリアルタイムのイラスト生成で応答する親子向けアプリケーションです。

単なる知識提供に留まらず、AI を触媒として親子のコミュニケーションを誘発し、受動的なスクリーンタイムを能動的で質の高い学びの時間へと変えることを目指します。

## ✨ コンセプト

子供の「なんで？」という質問に、物知り博士の「アイ」が分かりやすい解説とイラストで答えます。
このプロジェクトの最大の特徴は、AIの解説に加えて親子の会話を促す**「おはなしのタネ」**機能です。

これは、AIから始まった学びを親子間の対話へとつなげるための「問いかけのヒント」です。

**例:**
*   子どもが「どうして星はキラキラ光るの？」と質問
*   AIが解説（子ども向け）: 「お星さまはね、遠いところにあるから光がブルブル震えて見えるんだよ」
*   おはなしのタネ（保護者向け）: 「お星さまがウインクしてるみたいだね。なんてお話してるんだと思う？」

この「おはなしのタネ」があることで、保護者は子どもの想像力をさらに引き出す次の問いを自然に投げかけることができます。
これにより、単なるQ&Aツールから「AIが親子の対話をコーチングしてくれるアプリ」へと進化させ、親が抱える「スマホ育児への罪悪感」を「子どもと話すきっかけを得られるツール」へと転換します。

## 🛠️ 技術アーキテクチャ

Flutter (Web)製のフロントエンドと、Cloud Run 上で動作する Python 製のバックエンド（ADK: Agents Development Kit）で構成されています。

ユーザーの音声アップロードは、Cloud Functions for Firebase が発行する**署名付き URL**を利用して行われます。アップロードされたファイルは**Eventarc**を介して Cloud Run のバックエンド処理をトリガーし、処理結果は**Firestore**を通じてフロントエンドにリアルタイムで通知される、イベント駆動型のアーキテクチャを採用しています。

## 🚀 クイックスタート

このプロジェクトをローカルで開発・実行するための基本的な手順です。

1.  **リポジトリのクローン**:

    ```bash
    git clone <repository-url>
    cd coco-ai
    ```

2.  **Firebase 接続情報の設定 (フロントエンド)**:
    Flutter Web アプリの Firebase 設定は、ローカルでの実行時に環境変数として渡されます。プロジェクトのルートディレクトリに `config/dev.json` というファイルを作成し、Firebase コンソールから取得した Web アプリの設定を以下の形式で貼り付けます。
    `config/dev.example.json` をコピーして作成してください。

    **`config/dev.json` の内容:**

    ```json
    {
      "FIREBASE_API_KEY": "your-api-key",
      "FIREBASE_AUTH_DOMAIN": "your-project-id.firebaseapp.com",
      "FIREBASE_PROJECT_ID": "your-project-id",
      "FIREBASE_STORAGE_BUCKET": "your-project-id.firebasestorage.app",
      "FIREBASE_MESSAGING_SENDER_ID": "1234567890",
      "FIREBASE_APP_ID": "1:1234567890:web:abcdef1234567890"
    }
    ```

    このファイルは、`flutter run` コマンド実行時に `--dart-define-from-file` フラグで読み込まれます。Firebase Emulator Suite はバックエンドサービス（Functions, Firestore など）をローカルで模倣しますが、Flutter アプリが Firebase プロジェクト自体を認識し、接続するためには、これらの設定情報が依然として必要です。

3.  **各サービスのセットアップ**:
    `app`, `backend`, `functions` の各ディレクトリに移動し、それぞれの `README.md` に記載されている手順に従って、依存関係のインストールと仮想環境の構築を行ってください。

## ☁️ デプロイ

このプロジェクトのすべてのコンポーネント（Firebase Rules, Cloud Functions, Backend Service, Frontend App）は、**Cloud Build** を使用して一元的にデプロイされます。

デプロイは、リポジトリのルートにある `cloudbuild.yaml` に定義されたパイプラインに従って実行されます。変更を Git リポジトリのメインブランチにプッシュすると、Cloud Build トリガーが自動的に起動し、インフラ全体がビルド・デプロイされます。

### 手動でのデプロイ実行

手動で Cloud Build をトリガーする場合は、以下の `gcloud` コマンドを使用します。

```bash
gcloud builds submit --config cloudbuild.yaml .
```

### 部分的なデプロイ
`cloudbuild.yaml` の `_DEPLOY_TARGET` 置換変数を指定することで、特定のコンポーネントのみをデプロイできます。これは、特定のサービスのみを更新したい場合に便利です。

```bash
# フロントエンドアプリ (Flutter Web) のみデプロイ
gcloud builds submit --config cloudbuild.yaml --substitutions=_DEPLOY_TARGET=app .

# バックエンド (Cloud Run) と Eventarc トリガーのみデプロイ
gcloud builds submit --config cloudbuild.yaml --substitutions=_DEPLOY_TARGET=backend .
```

指定可能なターゲットは `app`, `rules`, `functions`, `backend`, `trigger` です。デフォルトは `all` です。

## 📂 ディレクトリ構成

- `./app`: Flutter で構築されたフロントエンドアプリケーションです。詳細は `app/README.md` を参照してください。
- `./backend`: Cloud Run 上で動作する Python のバックエンド（AI エージェント）です。詳細は `backend/README.md` を参照してください。
- `./functions`: フロントエンドからのリクエストに応じて、Cloud Storage へのアップロード用署名付き URL を発行する Python 製の Cloud Functions for Firebase です。詳細は `functions/README.md` を参照してください。
