# Coco-Ai Cloud Functions

> Google Cloud Japan AI Hackathon vol.3 応募作品

このディレクトリは、親子対話AI「Coco-Ai」プロジェクトで使用されるCloud Functionsのソースコードを格納します。

## 役割

Firebaseのイベントをトリガーとして、バックエンドのAIエージェント（Cloud Run）を呼び出す役割を担います。

- **イベントトリガー**: Firebase Storageに音声ファイルがアップロードされたことを検知します。
- **バックエンド連携**: 検知したイベント情報を元に、Cloud Runで動作しているバックエンドサービスへHTTPリクエストを送信し、AI処理を開始させます。

これにより、フロントエンドとバックエンドを疎結合に保ち、イベント駆動型のアーキテクチャを実現しています。