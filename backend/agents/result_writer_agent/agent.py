from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part
from models.agent_models import (
    ExplanationResult,
    FinalJobData,
    IllustrationResult,
    NarrationResult,
    TranscriptionResult,
)
from services.firestore_service import update_job_status
from services.logging_service import get_logger


class ResultWriterAgent(BaseAgent):
    """
    The final agent in the workflow, responsible for writing the results to Firestore.

    This agent inspects the session state for a `workflow_failed` flag or
    `parallel_errors` set by previous agents or callbacks.
    - If an error is detected, it updates the Firestore job document with a 'failed' status.
    - If successful, it gathers all the generated artifacts (transcription,
      explanation, image path, audio path), structures them, and updates the
      Firestore document with a 'completed' status and the final data.
    """

    def __init__(self):
        super().__init__(name="ResultWriterAgent")
        self.logger = get_logger(__name__)

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = context.session.state or {}
        job_id = state.get("job_id")
        if not job_id:
            raise ValueError("job_id not found in session state.")

        # Check for failure based on the 'workflow_failed' flag or the presence
        # of 'parallel_errors' from the ParallelAgent.
        if state.get("workflow_failed") or state.get("parallel_errors"):
            errors = state.get("parallel_errors") or {
                "unknown": "One or more agents failed"
            }
            error_message = f"Workflow failed: {errors}"
            self.logger.error(f"[{job_id}] {error_message}")
            await update_job_status(job_id, "error", {"errorMessage": error_message})
            # Raise an exception to ensure the overall process is marked as failed.
            raise RuntimeError(error_message)

        try:
            # Retrieve and validate the required results from the session state.
            transcription = TranscriptionResult.model_validate(state["transcription"])
            explanation_data = state["explanation_data"]
            illustration = IllustrationResult.model_validate(state["illustration"])
            narration = NarrationResult.model_validate(state["narration"])

            explanation = ExplanationResult(
                job_id=job_id,
                original_text=transcription.text,
                **explanation_data,
            )

            final_data_model = FinalJobData(
                transcribedText=transcription.text,
                childExplanation=explanation.child_explanation,
                parentHint=explanation.parent_hint,
                illustrationPrompt=explanation.illustration_prompt,
                imageGcsPath=illustration.image_gcs_path,
                finalAudioGcsPath=narration.final_audio_gcs_path,
            )
            await update_job_status(job_id, "completed", final_data_model.model_dump())

            final_message = f"Workflow for job {job_id} completed successfully."
            self.logger.info(
                f"[{job_id}] {final_message} Results written to Firestore."
            )

            # Return the final success message as an event.
            yield Event(
                author=self.name, content=Content(parts=[Part(text=final_message)])
            )

        except Exception as e:
            self.logger.error(
                f"[{job_id}] Error writing results to Firestore: {e}", exc_info=True
            )
            await update_job_status(
                job_id,
                "error",
                {"errorMessage": f"Final result processing failed: {e}"},
            )
            raise
