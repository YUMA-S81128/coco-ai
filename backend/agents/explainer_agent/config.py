from google.genai import types

# 使用するGeminiモデルのID
MODEL_ID = "gemini-2.5-flash"

# コンテンツの安全性を確保するためのセーフティ設定
# 特定のカテゴリの不適切なコンテンツをブロックする
SAFETY_SETTINGS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
]

# コンテンツ生成時の設定
GENERATE_CONFIG = types.GenerateContentConfig(
    safety_settings=SAFETY_SETTINGS,
    temperature=0.5,  # 生成されるテキストの多様性を制御 (0.0-1.0)
    max_output_tokens=500,  # 生成されるテキストの最大長
    top_p=0.9,  # Top-pサンプリング。単語の選択肢を絞る
    response_mime_type="application/json",  # レスポンス形式をJSONに指定
)
