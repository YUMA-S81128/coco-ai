from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    """音声テキスト変換の結果"""

    job_id: str
    gcs_uri: str
    text: str = Field(description="音声から変換されたテキスト")


class ExplanationOutput(BaseModel):
    """
    LLM (ExplainerAgent) が生成する解説データ。
    LlmAgentのoutput_schemaとして使用される。
    """

    child_explanation: str = Field(description="子供向けの解説文")
    child_explanation_ssml: str = Field(description="子供向けの解説文 (SSML形式)")
    parent_hint: str = Field(description="親向けの対話のヒント")
    illustration_prompt: str = Field(description="イラスト生成用の英語プロンプト")
    keywords: list[str] = Field(description="イラストの主要要素を表す英単語リスト")
    needs_clarification: bool = Field(description="追加の確認が必要かどうか")
    clarification_question: str | None = Field(
        default=None, description="追加の確認が必要な場合の質問文"
    )


class ExplanationResult(ExplanationOutput):
    """解説生成の結果全体。job_idなどを含む。"""

    job_id: str
    original_text: str


class IllustrationResult(BaseModel):
    """イラスト生成の結果"""

    job_id: str
    image_gcs_path: str = Field(description="生成されたイラストのGCSパス")


class NarrationResult(BaseModel):
    """音声合成の結果"""

    job_id: str
    final_audio_gcs_path: str = Field(description="生成された解説音声のGCSパス")


# ==============================
# リクエスト / レスポンス モデル
# ==============================
class JobRequest(BaseModel):
    prompt: str


class JobResponse(BaseModel):
    job_id: str
    status: str


class JobResultResponse(BaseModel):
    job_id: str
    status: str
    result: str | None = None
    gcs_output: str | None = None


# ==============================
# CloudEvent Models
# ==============================
class CloudEventMetadata(BaseModel):
    """CloudEventのmetadataフィールド"""

    jobId: str
    userId: str


class StorageObjectData(BaseModel):
    """CloudEventのdataフィールド (Storage Object)"""

    bucket: str
    name: str
    metadata: CloudEventMetadata
