from uuid import uuid4

from agents.base_processing_agent import BaseProcessingAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.cloud.texttospeech import SynthesisInput, TextToSpeechClient
from google.genai.types import Content, Part
from models.agent_models import NarrationResult
from services.logging_service import get_logger
from services.storage_service import upload_blob_from_memory

from config import get_settings

from .config import AUDIO_CONFIG, OPERATION_TIMEOUT, VOICE_SELECTION_PARAMS


class NarratorAgent(BaseProcessingAgent):
    """
    An agent that synthesizes speech from the explanation text.

    This agent uses the Google Cloud Text-to-Speech API to convert an SSML
    formatted string into an audio file (MP3) and uploads it to a
    Google Cloud Storage bucket.
    """

    def __init__(self):
        super().__init__(name="NarratorAgent")
        self.settings = get_settings()
        self.client = TextToSpeechClient()
        self.logger = get_logger(__name__)

    async def _run_async_impl(self, context: InvocationContext):
        """
        Generates audio from an SSML text and saves it to Cloud Storage.
        """
        job_id, explanation = self._get_common_data(context)
        ssml_text = explanation.child_explanation_ssml

        self.logger.info(f"[{job_id}] Starting speech synthesis (SSML): {ssml_text}")

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

            self.logger.info(f"[{job_id}] Speech synthesis completed: {gcs_path}")
            result = NarrationResult(job_id=job_id, final_audio_gcs_path=gcs_path)
            context.session.state["narration"] = result.model_dump()

            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="Narration generated successfully.")]),
            )

        except Exception as e:
            self.logger.error(
                f"[{job_id}] Text-to-Speech API error: {e}", exc_info=True
            )
            raise
