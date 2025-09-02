from uuid import uuid4

from google import genai
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from google.genai.types import Content, Part
from models.agent_models import ExplanationOutput, IllustrationResult
from services.logging_service import get_logger

from config import get_settings

from .config import GENERATE_CONFIG_PARAMS, IMAGEN_MODEL_ID


class IllustratorAgent(BaseAgent):
    """
    An agent that generates illustrations matching the provided explanation.

    This agent uses the Imagen model via the Vertex AI API to create an image
    based on a prompt. The generated image is saved directly to a specified
    Google Cloud Storage bucket.
    """

    def __init__(self):
        super().__init__(name="IllustratorAgent")
        self.settings = get_settings()
        self.model = IMAGEN_MODEL_ID
        self.logger = get_logger(__name__)

        self.client = genai.Client(
            vertexai=True,
            project=self.settings.google_cloud_project_id,
            location=self.settings.region,
        )

    async def _run_async_impl(self, context: InvocationContext):
        """
        Generates an illustration from a prompt and saves it to Cloud Storage.
        """
        job_id = context.session.state.get("job_id")
        explanation_data = context.session.state.get("explanation_data")

        if not job_id or not explanation_data:
            raise ValueError("job_id and explanation_data must be in session state.")

        explanation = ExplanationOutput.model_validate(explanation_data)
        prompt = explanation.illustration_prompt
        self.logger.info(
            f"[{job_id}] Starting illustration generation with prompt: {prompt}"
        )

        destination_blob_name = f"{job_id}-{uuid4()}.png"
        output_gcs_uri = (
            f"gs://{self.settings.generated_image_bucket}/{destination_blob_name}"
        )

        generate_config = types.GenerateImagesConfig(
            output_gcs_uri=output_gcs_uri, **GENERATE_CONFIG_PARAMS
        )

        try:
            images = self.client.models.generate_images(
                model=self.model, prompt=prompt, config=generate_config
            )

            if not images:
                raise ValueError("Image generation failed.")

            self.logger.info(f"[{job_id}] Illustration saved to GCS: {output_gcs_uri}")

            result = IllustrationResult(
                job_id=job_id,
                image_gcs_path=output_gcs_uri,
            )
            context.session.state["illustration"] = result.model_dump()
            yield Event(
                author=self.name,
                content=Content(
                    parts=[Part(text="Illustration generated successfully.")]
                ),
            )
        except Exception as e:
            self.logger.error(f"[{job_id}] Imagen API error: {e}", exc_info=True)
            raise
