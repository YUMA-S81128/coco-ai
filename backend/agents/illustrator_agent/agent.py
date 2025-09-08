from uuid import uuid4

from agents.base_processing_agent import BaseProcessingAgent
from google import genai
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from google.genai.types import Content, Part
from models.agent_models import IllustrationResult
from services.logging_service import get_logger

from config import get_settings

from .config import GENERATE_CONFIG_PARAMS, IMAGEN_MODEL_ID


class IllustratorAgent(BaseProcessingAgent):
    """
    提供された解説に合ったイラストを生成するエージェント。

    このエージェントは、Vertex AI API経由でImagenモデルを使用し、
    プロンプトに基づいて画像を生成する。生成された画像は指定された
    Google Cloud Storageバケットに直接保存される。
    """

    def __init__(self):
        super().__init__(name="IllustratorAgent")
        self.settings = get_settings()
        self.model = IMAGEN_MODEL_ID
        self.logger = get_logger(__name__)

        # Vertex AI APIを使用するクライアントを初期化
        self.client = genai.Client(
            vertexai=True,
            project=self.settings.google_cloud_project_id,
            location=self.settings.region,
        )

    async def _run_async_impl(self, context: InvocationContext):
        """
        プロンプトからイラストを生成し、Cloud Storageに保存する。
        """
        job_id, explanation = self._get_common_data(context)
        prompt = explanation.illustration_prompt
        self.logger.info(
            f"[{job_id}] イラスト生成を開始します。プロンプト: {prompt}"
        )

        # 保存先のGCSパスを生成
        destination_blob_name = f"{job_id}-{uuid4()}.png"
        output_gcs_uri = (
            f"gs://{self.settings.generated_image_bucket}/{destination_blob_name}"
        )

        # 画像生成の設定
        generate_config = types.GenerateImagesConfig(
            output_gcs_uri=output_gcs_uri, **GENERATE_CONFIG_PARAMS
        )

        try:
            # Imagenモデルを呼び出して画像を生成
            images = self.client.models.generate_images(
                model=self.model, prompt=prompt, config=generate_config
            )

            if not images:
                raise ValueError("画像生成に失敗しました。")

            self.logger.info(f"[{job_id}] イラストをGCSに保存しました: {output_gcs_uri}")

            # 結果をセッション状態に保存
            result = IllustrationResult(
                job_id=job_id,
                image_gcs_path=output_gcs_uri,
            )
            context.session.state["illustration"] = result.model_dump()
            yield Event(
                author=self.name,
                content=Content(
                    parts=[Part(text="イラストの生成に成功しました。")])
            )
        except Exception as e:
            self.logger.error(f"[{job_id}] Imagen APIでエラーが発生しました: {e}", exc_info=True)
            raise
