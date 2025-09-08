from google.cloud.speech_v2.types import cloud_speech

# Speech-to-Text APIの認識設定
RECOGNITION_CONFIG = cloud_speech.RecognitionConfig(
    # デコーディング設定を自動検出
    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
    # 使用するモデル（longは長時間の音声ファイル向け）
    model="long",
    # 言語コード（日本語）
    language_codes=["ja-JP"],
)

# API呼び出しのタイムアウト時間（秒）
OPERATION_TIMEOUT: int = 180
