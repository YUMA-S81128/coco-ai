from google.genai import types

# 使用するImagenモデルのID
IMAGEN_MODEL_ID = "imagen-4.0-fast-generate-001"

# 画像生成の基本設定
# この辞書は、agent.pyで動的に`output_gcs_uri`が追加されてから利用されます。
GENERATE_CONFIG_PARAMS = {
    # 生成する画像の数
    "number_of_images": 1,
    # 画像のアスペクト比（1:1は正方形）
    "aspect_ratio": "1:1",
    # プロンプトへの忠実度を制御（5〜12の範囲で設定）
    "guidance_scale": 7.0,
    # 生成する画像のサイズ
    "image_size": "1K",
    # セーフティフィルターの強度
    "safety_filter_level": types.SafetyFilterLevel.BLOCK_LOW_AND_ABOVE,
    # 人物生成の許可設定（許可しない）
    "person_generation": types.PersonGeneration.DONT_ALLOW,
    # プロンプトの言語
    "language": types.ImagePromptLanguage.ja,
    # 出力される画像のMIMEタイプ
    "output_mime_type": "image/png",
    # 安全性に関する属性情報を含めるか
    "include_safety_attributes": True,
    # RAI（Responsible AI）に関する理由を含めるか
    "include_rai_reason": True,
    # 生成画像に透かしを追加するか
    "add_watermark": True,
}
