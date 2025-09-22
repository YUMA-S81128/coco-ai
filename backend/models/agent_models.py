from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    """音声文字起こしプロセスの結果"""

    job_id: str
    gcs_uri: str
    text: str = Field(description="音声から書き起こされたテキスト")


class ExplanationOutput(BaseModel):
    """
    ExplainerAgent内のLLMによって生成される構造化データ。
    このモデルは、LlmAgentの `output_schema` として使用され、
    JSON出力形式を強制する。
    """

    child_explanation: str = Field(description="子供向けの解説文")
    child_explanation_ssml: str = Field(description="子供向けの解説文 (SSML形式)")
    parent_hint: str = Field(description="親向けの対話のヒント")
    illustration_prompt: str = Field(description="イラスト生成用の日本語プロンプト")
    needs_clarification: bool = Field(description="追加の確認が必要かどうか")
    clarification_question: str | None = Field(
        default=None, description="追加の確認が必要な場合の質問文"
    )


class ExplanationResult(ExplanationOutput):
    """メタデータを含む、解説生成プロセスの完全な結果"""

    job_id: str
    original_text: str


class IllustrationResult(BaseModel):
    """イラスト生成プロセスの結果"""

    job_id: str
    image_gcs_path: str = Field(description="生成されたイラストのGCSパス")


class NarrationResult(BaseModel):
    """音声合成プロセスの結果"""

    job_id: str
    final_audio_gcs_path: str = Field(description="生成されたナレーション音声のGCSパス")


class FinalJobData(BaseModel):
    """ジョブ完了時にFirestoreに書き込まれる最終的なデータ構造"""

    transcribedText: str
    childExplanation: str
    parentHint: str
    illustrationPrompt: str
    imageGcsPath: str
    finalAudioGcsPath: str


class CloudEventMetadata(BaseModel):
    """CloudEventデータペイロード内の `metadata` フィールド"""

    job_id: str
    user_id: str


class StorageObjectData(BaseModel):
    """Cloud StorageからのCloudEventの `data` フィールド"""

    bucket: str
    name: str
    metadata: CloudEventMetadata
