from google.cloud import texttospeech

VOICE_SELECTION_PARAMS = texttospeech.VoiceSelectionParams(
    language_code="ja-JP",
    name="ja-JP-Wavenet-A",
)

AUDIO_CONFIG = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

OPERATION_TIMEOUT: int = 180
