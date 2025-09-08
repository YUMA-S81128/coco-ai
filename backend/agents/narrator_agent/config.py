from google.cloud import texttospeech

# 音声合成に使用する声の設定
VOICE_SELECTION_PARAMS = texttospeech.VoiceSelectionParams(
    language_code="ja-JP",  # 言語コード (日本語)
    name="ja-JP-Wavenet-A",  # 音声モデル名
)

# 出力する音声ファイルの設定
AUDIO_CONFIG = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3  # 音声エンコーディング (MP3)
)

# API呼び出しのタイムアウト時間（秒）
OPERATION_TIMEOUT: int = 180
