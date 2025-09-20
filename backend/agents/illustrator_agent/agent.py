from uuid import uuid4

from agents.base_processing_agent import BaseProcessingAgent
from google import genai
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from google.genai.types import Content, Part
from models.agent_models import IllustrationResult
from services.firestore_session_service import FirestoreSessionService
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
        self._settings = get_settings()
        self._model = IMAGEN_MODEL_ID
        self._logger = get_logger(__name__)

        # Vertex AI APIを使用するクライアントを初期化
        self._client = genai.Client(
            vertexai=True,
            project=self._settings.google_cloud_project,
            location=self._settings.google_cloud_location,
        )

    async def _run_async_impl(self, context: InvocationContext):
        """
        プロンプトからイラストを生成し、Cloud Storageに保存する。
        """
        job_id, explanation = await self._get_common_data(context)
        user_id = context.session.user_id
        prompt = explanation.illustration_prompt
        self._logger.info(f"[{job_id}] イラスト生成を開始します。プロンプト: {prompt}")

        # 保存先のGCSパスを生成
        destination_blob_name = f"{user_id}/{job_id}/{uuid4()}.png"
        output_gcs_uri = (
            f"gs://{self._settings.generated_image_bucket}/{destination_blob_name}"
        )

        # 画像生成の設定
        generate_config = types.GenerateImagesConfig(
            output_gcs_uri=output_gcs_uri, **GENERATE_CONFIG_PARAMS
        )

        try:
            # Imagenモデルを呼び出して画像を生成
            response = self._client.models.generate_images(
                model=self._model, prompt=prompt, config=generate_config
            )

            # --- デバッグログ ---
            if response and response.generated_images:
                self._logger.info(
                    f"デバッグ (image.image object): {dir(response.generated_images[0].image)}"
                )
            # --- デバッグログ終 ---

            if not response.generated_images:
                raise ValueError("画像生成に失敗しました。")

            self._logger.info(
                f"[{job_id}] イラストをGCSに保存しました: {output_gcs_uri}"
            )

            result = IllustrationResult(
                job_id=job_id,
                image_gcs_path=output_gcs_uri,
            )

            # メモリ上のセッション状態をまず更新
            context.session.state["illustration"] = result

            # update_sessionを直接呼び出し、状態の永続化を待つ
            try:
                self._logger.info(
                    f"[{job_id}] イラスト結果をセッションに永続化します..."
                )
                session_service = context.session_service
                assert isinstance(session_service, FirestoreSessionService)

                updated_session = await session_service.update_session(
                    session_id=context.session.id,
                    state_delta={"illustration": result},
                    app_name=context.session.app_name,
                    user_id=context.session.user_id,
                )
                if not updated_session:
                    raise RuntimeError(
                        "セッションの更新に失敗しました (update_session returned None)"
                    )
                self._logger.info(f"[{job_id}] セッションの永続化が完了しました。")
            except Exception as e:
                self._logger.error(
                    f"[{job_id}] セッションの永続化中にエラーが発生しました: {e}",
                    exc_info=True,
                )
                raise

            # 状態更新を含まない、単純な完了イベントをyieldする
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="イラストの生成に成功しました。")]),
            )

        except Exception as e:
            self._logger.error(
                f"[{job_id}] Imagen APIでエラーが発生しました: {e}", exc_info=True
            )
            raise
