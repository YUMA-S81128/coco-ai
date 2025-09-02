from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part
from models.agent_models import (
    ExplanationResult,
    IllustrationResult,
    NarrationResult,
    TranscriptionResult,
)
from services.firestore_service import update_job_status
from services.logging_service import get_logger


class ResultWriterAgent(BaseAgent):
    """
    ワークフローの最終結果をFirestoreに書き込むエージェント。
    - context.session.state に保持されているフラグやエラー情報を参照
    - workflow_failed が True なら失敗として Firestore に記録
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

        # workflow_failed フラグまたは parallel_errors の有無で判定
        if state.get("workflow_failed") or state.get("parallel_errors"):
            errors = state.get("parallel_errors") or {
                "unknown": "One or more agents failed"
            }
            self.logger.error(f"[{job_id}] Workflow failed: {errors}")
            await update_job_status(job_id, "failed", {"errors": errors})
            raise RuntimeError(f"Workflow failed: {errors}")

        try:
            # 必須結果の取得とバリデーション
            transcription = TranscriptionResult.model_validate(state["transcription"])
            explanation_data = state["explanation_data"]
            illustration = IllustrationResult.model_validate(state["illustration"])
            narration = NarrationResult.model_validate(state["narration"])

            explanation = ExplanationResult(
                job_id=job_id,
                original_text=transcription.text,
                **explanation_data,
            )

            final_data = {
                "transcription": transcription.model_dump(),
                "explanation": explanation.model_dump(),
                "illustration": illustration.model_dump(),
                "narration": narration.model_dump(),
            }
            await update_job_status(job_id, "completed", final_data)

            final_message = f"Workflow for job {job_id} completed successfully."
            self.logger.info(
                f"[{job_id}] {final_message} Results written to Firestore."
            )

            # 最終結果をイベントとして返す
            yield Event(
                author=self.name, content=Content(parts=[Part(text=final_message)])
            )

        except Exception as e:
            self.logger.error(
                f"[{job_id}] Error writing results to Firestore: {e}", exc_info=True
            )
            await update_job_status(
                job_id, "failed", {"errors": {"result_writer": str(e)}}
            )
            raise
