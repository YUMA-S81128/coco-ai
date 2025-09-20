from urllib.parse import urlparse
from uuid import uuid4

from agents.base_processing_agent import BaseProcessingAgent
from google import genai
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from google.genai.types import Content, Part
from models.agent_models import IllustrationResult
from services import storage_service
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

        # 最終的な保存先のファイル名を定義
        destination_blob_name = f"{user_id}/{job_id}/{uuid4()}.png"

        # APIへ渡す一時的な出力先「ディレクトリ」を定義
        output_gcs_directory = (
            f"gs://{self._settings.generated_image_bucket}/temp_generations/{job_id}/"
        )

        # 画像生成の設定
        generate_config = types.GenerateImagesConfig(
            output_gcs_uri=output_gcs_directory, **GENERATE_CONFIG_PARAMS
        )

        try:
            # Imagenモデルを呼び出して画像を生成
            response = self._client.models.generate_images(
                model=self._model, prompt=prompt, config=generate_config
            )

            self._logger.info(f"debug (original response): {response}")

            if not response.generated_images:
                raise ValueError("画像生成に失敗しました。")

            generated_image = response.generated_images[0]
            if not generated_image.image or not generated_image.image.gcs_uri:
                raise ValueError("生成された画像にGCS URIが含まれていません。")

            # 画像は一時的なGCSパスに保存される
            temp_gcs_uri = generated_image.image.gcs_uri
            self._logger.info(
                f"[{job_id}] イラストを一時GCSパスに保存しました: {temp_gcs_uri}"
            )

            # 一時パスをパースしてバケットとBlob名を取得
            parsed_uri = urlparse(temp_gcs_uri)
            temp_bucket_name = parsed_uri.netloc
            temp_blob_name = parsed_uri.path.lstrip("/")

            # GCS内でファイルを目的のパスに移動
            final_gcs_uri = await storage_service.rename_blob(
                bucket_name=temp_bucket_name,
                blob_name=temp_blob_name,
                new_name=destination_blob_name,
            )
            self._logger.info(
                f"[{job_id}] イラストを目的のGCSパスに移動しました: {final_gcs_uri}"
            )

            result = IllustrationResult(
                job_id=job_id,
                image_gcs_path=final_gcs_uri,
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
