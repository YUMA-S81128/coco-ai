from uuid import uuid4

from agents.base_processing_agent import BaseProcessingAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.cloud.texttospeech import SynthesisInput, TextToSpeechClient
from google.genai.types import Content, Part
from models.agent_models import NarrationResult
from services.firestore_session_service import FirestoreSessionService
from services.logging_service import get_logger
from services.storage_service import upload_blob_from_memory

from config import get_settings

from .config import AUDIO_CONFIG, OPERATION_TIMEOUT, VOICE_SELECTION_PARAMS


class NarratorAgent(BaseProcessingAgent):
    """
    解説テキストから音声を合成するエージェント。

    このエージェントは、Google Cloud Text-to-Speech APIを使用して、
    SSML形式の文字列を音声ファイル（MP3）に変換し、
    Google Cloud Storageバケットにアップロードする。
    """

    def __init__(self):
        super().__init__(name="NarratorAgent")
        self._settings = get_settings()
        self._client = TextToSpeechClient()
        self._logger = get_logger(__name__)

    async def _run_async_impl(self, context: InvocationContext):
        """
        SSMLテキストから音声を生成し、Cloud Storageに保存する。
        """
        job_id, explanation = await self._get_common_data(context)
        ssml_text = explanation.child_explanation_ssml

        self._logger.info(f"[{job_id}] 音声合成を開始します (SSML): {ssml_text}")

        try:
            synthesis_input = SynthesisInput(ssml=ssml_text)

            # Text-to-Speech APIを呼び出し
            response = self._client.synthesize_speech(
                input=synthesis_input,
                voice=VOICE_SELECTION_PARAMS,
                audio_config=AUDIO_CONFIG,
                timeout=OPERATION_TIMEOUT,
            )

            # GCSにアップロード
            file_name = f"{job_id}-{uuid4()}.mp3"
            gcs_path = await upload_blob_from_memory(
                bucket_name=self._settings.processed_audio_bucket,
                destination_blob_name=file_name,
                data=response.audio_content,
                content_type="audio/mpeg",
            )

            self._logger.info(f"[{job_id}] 音声合成が完了しました: {gcs_path}")

            result = NarrationResult(job_id=job_id, final_audio_gcs_path=gcs_path)

            # メモリ上のセッション状態をまず更新
            context.session.state["narration"] = result

            # update_sessionを直接呼び出し、状態の永続化を待つ
            try:
                self._logger.info(f"[{job_id}] ナレーション結果をセッションに永続化します...")
                session_service = context.session_service
                assert isinstance(session_service, FirestoreSessionService)

                updated_session = await session_service.update_session(
                    session_id=context.session.id,
                    state_delta={"narration": result},
                    app_name=context.session.app_name,
                    user_id=context.session.user_id,
                )
                if not updated_session:
                    raise RuntimeError("セッションの更新に失敗しました (update_session returned None)")
                self._logger.info(f"[{job_id}] セッションの永続化が完了しました。")
            except Exception as e:
                self._logger.error(
                    f"[{job_id}] セッションの永続化中にエラーが発生しました: {e}", exc_info=True
                )
                raise

            # 状態更新を含まない、単純な完了イベントをyieldする
            yield Event(
                author=self.name,
                content=Content(
                    parts=[Part(text="ナレーションの生成に成功しました。")]
                ),
            )

        except Exception as e:
            self._logger.error(
                f"[{job_id}] Text-to-Speech APIでエラーが発生しました: {e}",
                exc_info=True,
            )
            raise
