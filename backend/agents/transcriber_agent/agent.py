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
    An agent that transcribes audio files to text using Google Cloud Speech-to-Text.
    """

    def __init__(self):
        super().__init__(name="TranscriberAgent")
        self.settings = get_settings()
        self.speech_client = SpeechClient()
        self.logger = get_logger(__name__)

    async def _run_async_impl(self, context: InvocationContext):
        """
        The main execution logic for the agent.
        """
        job_id = context.session.state.get("job_id")
        gcs_uri = context.session.state.get("gcs_uri")

        if not job_id or not gcs_uri:
            raise ValueError(
                "job_id and gcs_uri must be provided in the session state."
            )

        self.logger.info(f"[{job_id}] Starting audio transcription for: {gcs_uri}")

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
                self.logger.warning(f"[{job_id}] Could not extract text from audio.")
                raise ValueError("Transcription resulted in empty text.")

            self.logger.info(f"[{job_id}] Transcribed text: {transcript}")

            # Store the transcribed text for the ExplainerAgent's prompt template.
            context.session.state["transcribed_text"] = transcript

            # Store a structured result object for the final ResultWriterAgent.
            result = TranscriptionResult(
                job_id=job_id, gcs_uri=gcs_uri, text=transcript
            )
            context.session.state["transcription"] = result.model_dump()

            # Subsequent agents receive the text via session.state and the prompt
            # template ({transcribed_text}). To avoid affecting the conversation
            # history with the raw text, this agent only yields a simple
            # completion notification.
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
            error_message = f"An error occurred during audio transcription: {e}"
            self.logger.error(f"[{job_id}] {error_message}", exc_info=True)
            raise
