# 親子対話 AI「Coco-Ai」

> Google Cloud Japan AI Hackathon vol.3 応募作品

> 子供の「なんで？」が、親子の最高の学びに変わる

Coco-Ai は、子供の尽きない好奇心に対し、2 人のキャラクター「ココ」と「アイ」が対話とリアルタイムのイラスト生成で応答する親子向けアプリケーションです。

単なる知識提供に留まらず、AI を触媒として親子のコミュニケーションを誘発し、受動的なスクリーンタイムを能動的で質の高い学びの時間へと変えることを目指します。

## ✨ コンセプト

子供の「なんで？」という質問に、物知り博士の「アイ」が分かりやすい解説とイラストで答えます。
このプロジェクトの最大の特徴は、**親の画面にだけ表示される「対話を広げるヒント」機能**です。

**例:**

- **子供の画面:** クジラの絵と「クジラは海で一番大きな動物なんだよ」という解説
- **親の画面:** 「『クジラさんの夢ってどんなだろうね？』と聞いてみましょう！」というヒント

これにより、単なる Q&A ツールから「AI が親子の対話をコーチングしてくれるアプリ」へと進化させ、親が抱える「スマホ育児への罪悪感」を「子供と話すきっかけを得られるツール」へと転換します。

## 🛠️ 技術アーキテクチャ

Flutter (Web)製のフロントエンドと、Cloud Run 上で動作する Python 製のバックエンド（ADK: Agents Development Kit）で構成されています。

ユーザーの音声アップロードは、Cloud Functions for Firebase が発行する**署名付き URL**を利用して行われます。アップロードされたファイルは**Eventarc**を介して Cloud Run のバックエンド処理をトリガーし、処理結果は**Firestore**を通じてフロントエンドにリアルタイムで通知される、イベント駆動型のアーキテクチャを採用しています。

## 🚀 クイックスタート

このプロジェクトをローカルで実行するための基本的な手順です。

1.  **リポジトリのクローン**:

    ```bash
    git clone <repository-url>
    cd coco-ai
    ```

2.  **Firebase 接続情報の設定 (フロントエンド)**:
    Flutter Web アプリの Firebase 設定は、ビルド時に環境変数として渡されます。プロジェクトのルートディレクトリに `config/dev.json` というファイルを作成し、Firebase コンソールから取得した Web アプリの設定を以下の形式で貼り付けます。

    **`config/dev.json` の内容:**

    ```json
    {
      "FIREBASE_API_KEY": "AIzaSy...",
      "FIREBASE_AUTH_DOMAIN": "your-project-id.firebaseapp.com",
      "FIREBASE_PROJECT_ID": "your-project-id",
      "FIREBASE_STORAGE_BUCKET": "your-project-id.appspot.com",
      "FIREBASE_MESSAGING_SENDER_ID": "1234567890",
      "FIREBASE_APP_ID": "1:1234567890:web:abcdef1234567890"
    }
    ```

    このファイルは、`flutter run` コマンド実行時に `--dart-define-from-file` フラグで読み込まれます。詳細は `app/README.md` を参照してください。

3.  **各サービスのセットアップ**:
    `app`, `backend`, `functions` の各ディレクトリに移動し、それぞれの `README.md` に記載されている手順に従って、依存関係のインストールと仮想環境の構築を行ってください。

## 📂 ディレクトリ構成

- `./app`: Flutter で構築されたフロントエンドアプリケーションです。詳細は `app/README.md` を参照してください。
- `./backend`: Cloud Run 上で動作する Python のバックエンド（AI エージェント）です。詳細は `backend/README.md` を参照してください。
- `./functions`: フロントエンドからのリクエストに応じて、Cloud Storage へのアップロード用署名付き URL を発行する Python 製の Cloud Functions for Firebase です。詳細は `functions/README.md` を参照してください。
