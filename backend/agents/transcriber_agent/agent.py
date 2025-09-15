from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.genai.types import Content, Part
from models.agent_models import TranscriptionResult
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
        self.speech_client = SpeechClient()
        self.logger = get_logger(__name__)

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

        self.logger.info(f"[{job_id}] 音声の文字起こしを開始します: {gcs_uri}")

        try:
            # Speech-to-Textへのリクエストを作成
            request = cloud_speech.RecognizeRequest(
                recognizer=f"projects/{self._settings.google_cloud_project_id}/locations/global/recognizers/_",
                config=RECOGNITION_CONFIG,
                uri=gcs_uri,
            )

            # APIを呼び出し
            response = self.speech_client.recognize(
                request=request, timeout=OPERATION_TIMEOUT
            )

            # 結果から書き起こしテキストを抽出
            transcript = "".join(
                result.alternatives[0].transcript for result in response.results
            )

            if not transcript:
                self.logger.warning(
                    f"[{job_id}] 音声からテキストを抽出できませんでした。"
                )
                raise ValueError("文字起こしの結果が空です。")

            self.logger.info(f"[{job_id}] 書き起こしテキスト: {transcript}")

            # ExplainerAgentのプロンプトテンプレート用に、書き起こしたテキストを保存する。
            context.session.state["transcribed_text"] = transcript

            # 最終的なResultWriterAgent用に、構造化された結果オブジェクトを保存する。
            result = TranscriptionResult(
                job_id=job_id, gcs_uri=gcs_uri, text=transcript
            )
            context.session.state["transcription"] = result.model_dump()

            # 後続のエージェントは、session.stateとプロンプトテンプレート({transcribed_text})を介して
            # テキストを受け取ります。会話履歴に生テキストが影響を与えないように、
            # このエージェントは単純な完了通知のみを返す。
            yield Event(
                author=self.name,
                content=Content(
                    parts=[
                        Part(
                            text="文字起こしが完了し、テキストがセッション状態に保存されました。"
                        )
                    ]
                ),
            )

        except Exception as e:
            error_message = f"音声の文字起こし中にエラーが発生しました: {e}"
            self.logger.error(f"[{job_id}] {error_message}", exc_info=True)
            raise
