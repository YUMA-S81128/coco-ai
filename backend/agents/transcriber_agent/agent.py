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
    Google Cloud Speech-to-Textを使用して音声ファイルをテキストに変換するエージェント。
    """

    def __init__(self):
        super().__init__(name="TranscriberAgent")
        self.settings = get_settings()
        self.speech_client = SpeechClient()
        self.logger = get_logger(__name__)

    async def _run_async_impl(self, context: InvocationContext):
        """エージェントの実行ロジック"""
        job_id = context.session.state.get("job_id")
        gcs_uri = context.session.state.get("gcs_uri")

        if not job_id or not gcs_uri:
            raise ValueError(
                "job_id and gcs_uri must be provided in the session state."
            )

        self.logger.info(f"[{job_id}] 音声テキスト変換を開始: {gcs_uri}")

        try:
            request = cloud_speech.RecognizeRequest(
                recognizer=f"projects/{self.settings.google_cloud_project_id}/locations/global/recognizers/_",
                config=RECOGNITION_CONFIG,
                uri=gcs_uri,
            )

            response = self.speech_client.recognize(
                request=request, timeout=OPERATION_TIMEOUT
            )

            transcript = "".join(
                result.alternatives[0].transcript for result in response.results
            )

            if not transcript:
                self.logger.warning(
                    f"[{job_id}] 音声からテキストを抽出できませんでした。"
                )
                raise ValueError("Transcription resulted in empty text.")

            self.logger.info(f"[{job_id}] 変換されたテキスト: {transcript}")

            # ExplainerAgentのプロンプトテンプレート用
            context.session.state["transcribed_text"] = transcript

            # ResultWriterAgentが最終結果を書き込むためのオブジェクト
            result = TranscriptionResult(
                job_id=job_id, gcs_uri=gcs_uri, text=transcript
            )
            context.session.state["transcription"] = result.model_dump()

            # 後続のエージェントは session.state とプロンプトテンプレート ({transcribed_text}) を
            # 使ってテキストを受け取るため、会話履歴に影響を与えないよう、ここでは処理完了の通知のみを行う。
            yield Event(
                author=self.name,
                content=Content(
                    parts=[
                        Part(
                            text="Transcription completed and text stored in session state."
                        )
                    ]
                ),
            )

        except Exception as e:
            error_message = f"音声テキスト変換中にエラーが発生しました: {e}"
            self.logger.error(f"[{job_id}] {error_message}", exc_info=True)
            raise
