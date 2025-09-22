from dependencies import get_firestore_client
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.genai.types import Content, Part
from models.agent_models import TranscriptionResult
from services.firestore_service import update_job_data
from services.logging_service import get_logger

from config import get_settings

from .config import OPERATION_TIMEOUT, RECOGNITION_CONFIG


class TranscriberAgent(BaseAgent):
    """
    Google Cloud Speech-to-Textを使用して音声ファイルをテキストに書き起こすエージェント。
    """

    def __init__(self):
        super().__init__(name="TranscriberAgent")
        self._settings = get_settings()
        self._speech_client = SpeechClient()
        self._logger = get_logger(__name__)

    async def _run_async_impl(self, context: InvocationContext):
        """
        エージェントのメイン実行ロジック。
        """
        job_id = context.session.state.get("job_id")
        gcs_uri = context.session.state.get("gcs_uri")

        if not job_id or not gcs_uri:
            raise ValueError(
                "セッション状態には job_id と gcs_uri を提供する必要があります。"
            )

        self._logger.info(f"[{job_id}] 音声の文字起こしを開始します: {gcs_uri}")

        try:
            # Speech-to-Textへのリクエストを作成
            request = cloud_speech.RecognizeRequest(
                recognizer=f"projects/{self._settings.google_cloud_project}/locations/global/recognizers/_",
                config=RECOGNITION_CONFIG,
                uri=gcs_uri,
            )

            # APIを呼び出し
            response = self._speech_client.recognize(
                request=request, timeout=OPERATION_TIMEOUT
            )

            # 結果から書き起こしテキストを抽出
            transcript = "".join(
                result.alternatives[0].transcript for result in response.results
            )

            if not transcript:
                self._logger.warning(
                    f"[{job_id}] 音声からテキストを抽出できませんでした。"
                )
                raise ValueError("文字起こしの結果が空です。")

            self._logger.info(f"[{job_id}] 書き起こしテキスト: {transcript}")

            result = TranscriptionResult(
                job_id=job_id, gcs_uri=gcs_uri, text=transcript
            )

            # メモリ上のセッション状態をまず更新
            context.session.state["transcribed_text"] = transcript
            context.session.state["transcription"] = result

            # セッションとジョブの状態を更新
            try:
                # 1. adk_sessions ドキュメントを更新
                self._logger.info(f"[{job_id}] 文字起こし結果をセッションに永続化します...")
                session_service = context.session_service
                if hasattr(session_service, "update_session"):
                    update_session_func = getattr(session_service, "update_session")
                    updated_session = await update_session_func(
                        session_id=context.session.id,
                        state_delta={
                            "transcribed_text": transcript,
                            "transcription": result,
                        },
                        app_name=context.session.app_name,
                        user_id=context.session.user_id,
                    )
                    if not updated_session:
                        raise RuntimeError(
                            "セッションの更新に失敗しました (update_session returned None)"
                        )
                else:
                    self._logger.warning(
                        "session_service does not have update_session method. "
                        "State will be persisted by the next event."
                    )
                self._logger.info(f"[{job_id}] セッションの永続化が完了しました。")

                # 2. jobs ドキュメントを更新してUIに中間結果を通知
                self._logger.info(f"[{job_id}] jobsコレクションに中間結果を書き込みます...")
                db_client = get_firestore_client()
                await update_job_data(
                    db=db_client,
                    job_id=job_id,
                    data={"transcribedText": transcript}, # フロントのモデルに合わせてキャメルケースに
                )
                self._logger.info(f"[{job_id}] jobsコレクションの中間結果書き込みが完了しました。")

            except Exception as e:
                self._logger.error(
                    f"[{job_id}] 状態の永続化中にエラーが発生しました: {e}",
                    exc_info=True,
                )
                raise

            # 状態更新を含まない、単純な完了イベントをyieldする
            yield Event(
                author=self.name,
                content=Content(
                    parts=[
                        Part(text="文字起こしが完了し、結果をFirestoreに保存しました。")
                    ]
                ),
            )

        except Exception as e:
            error_message = f"音声の文字起こし中にエラーが発生しました: {e}"
            self._logger.error(f"[{job_id}] {error_message}", exc_info=True)
            raise
