from uuid import uuid4

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.cloud.texttospeech import SynthesisInput, TextToSpeechClient
from google.genai.types import Content, Part
from models.agent_models import ExplanationOutput, NarrationResult
from services.logging_service import get_logger
from services.storage_service import upload_blob_from_memory

from config import get_settings

from .config import AUDIO_CONFIG, OPERATION_TIMEOUT, VOICE_SELECTION_PARAMS


class NarratorAgent(BaseAgent):
    """
    解説文を音声に合成するエージェント。
    """

    def __init__(self):
        super().__init__(name="NarratorAgent")
        self.settings = get_settings()
        self.client = TextToSpeechClient()
        self.logger = get_logger(__name__)

    async def _run_async_impl(self, context: InvocationContext):
        """解説文から音声を生成し、Cloud Storageに保存する"""
        job_id = context.session.state.get("job_id")
        explanation_data = context.session.state.get("explanation_data")

        if not job_id or not explanation_data:
            raise ValueError("job_id and explanation_data must be in session state.")

        explanation = ExplanationOutput.model_validate(explanation_data)
        ssml_text = explanation.child_explanation_ssml

        self.logger.info(f"[{job_id}] 音声合成を開始 (SSML): {ssml_text}")

        try:
            synthesis_input = SynthesisInput(ssml=ssml_text)

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=VOICE_SELECTION_PARAMS,
                audio_config=AUDIO_CONFIG,
                timeout=OPERATION_TIMEOUT,
            )

            file_name = f"{job_id}-{uuid4()}.mp3"
            gcs_path = await upload_blob_from_memory(
                bucket_name=self.settings.processed_audio_bucket,
                destination_blob_name=file_name,
                data=response.audio_content,
                content_type="audio/mpeg",
            )

            self.logger.info(f"[{job_id}] 音声生成完了: {gcs_path}")
            result = NarrationResult(job_id=job_id, final_audio_gcs_path=gcs_path)
            context.session.state["narration"] = result.model_dump()

            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="Narration generated successfully.")]),
            )

        except Exception as e:
            self.logger.error(
                f"[{job_id}] Text-to-Speech APIエラー: {e}", exc_info=True
            )
            raise
