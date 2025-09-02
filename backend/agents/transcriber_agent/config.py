from google.cloud.speech_v2.types import cloud_speech

RECOGNITION_CONFIG = cloud_speech.RecognitionConfig(
    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
    model="long",
    language_codes=["ja-JP"],
)

OPERATION_TIMEOUT: int = 180
