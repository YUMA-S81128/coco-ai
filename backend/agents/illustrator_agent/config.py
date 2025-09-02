from google.genai import types

IMAGEN_MODEL_ID = "imagen-4.0-fast-generate-001"

# 画像生成の基本設定を辞書として定義
# agent.pyで動的にoutput_gcs_uriを追加して利用します
GENERATE_CONFIG_PARAMS = {
    "number_of_images": 1,
    "aspect_ratio": "1:1",
    # 5~12で設定する
    "guidance_scale": 7.0,
    "image_size": "1K",
    "safety_filter_level": types.SafetyFilterLevel.BLOCK_LOW_AND_ABOVE,
    "person_generation": types.PersonGeneration.DONT_ALLOW,
    "language": types.ImagePromptLanguage.ja,
    "output_mime_type": "image/png",
    "include_safety_attributes": True,
    "include_rai_reason": True,
    "add_watermark": True,
}
