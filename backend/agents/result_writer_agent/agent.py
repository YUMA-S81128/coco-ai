from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.cloud import firestore
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
    ワークフローの最終エージェント。結果をFirestoreに書き込む。

    このエージェントは、先行するエージェントやコールバックによって設定された
    `workflow_failed` フラグや `parallel_errors` をセッション状態から確認する。
    - エラーが検出された場合、Firestoreのジョブドキュメントを 'failed' ステータスで更新する。
    - 成功した場合、生成されたすべての成果物（文字起こし、解説、画像パス、音声パス）を
      収集・構造化し、Firestoreドキュメントを 'completed' ステータスと最終データで更新する。
    """

    def __init__(self, db_client: firestore.AsyncClient):
        super().__init__(name="ResultWriterAgent")
        self._logger = get_logger(__name__)
        self._db_client = db_client

    async def _run_async_impl(
        self, context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # ParallelAgentの実行後、最新の状態を確実にするためにセッションを再取得する
        session_service = context.session_service
        session = await session_service.get_session(
            app_name=context.session.app_name,
            user_id=context.session.user_id,
            session_id=context.session.id,
        )
        state = session.state if session else {}
        job_id = state.get("job_id")
        if not job_id:
            raise ValueError("セッション状態にjob_idが見つかりません。")

        # `workflow_failed` フラグまたは `parallel_errors` の存在に基づいて失敗をチェック
        if state.get("workflow_failed") or state.get("parallel_errors"):
            errors = state.get("parallel_errors") or {
                "unknown": "1つ以上のエージェントが失敗しました"
            }
            error_message = f"ワークフローが失敗しました: {errors}"
            self._logger.error(f"[{job_id}] {error_message}")
            await update_job_status(
                self._db_client, job_id, "error", {"errorMessage": error_message}
            )
            # プロセス全体が失敗としてマークされるように例外を発生させる
            raise RuntimeError(error_message)

        try:
            # セッション状態から必要な結果を取得して検証
            transcription = TranscriptionResult.model_validate(state["transcription"])
            explanation_data = state["explanation_data"]
            illustration = IllustrationResult.model_validate(state["illustration"])
            narration = NarrationResult.model_validate(state["narration"])

            explanation = ExplanationResult(
                job_id=job_id,
                original_text=transcription.text,
                **explanation_data,
            )

            # 最終的なデータモデルを構築
            final_data_model = FinalJobData(
                transcribedText=transcription.text,
                childExplanation=explanation.child_explanation,
                parentHint=explanation.parent_hint,
                illustrationPrompt=explanation.illustration_prompt,
                imageGcsPath=illustration.image_gcs_path,
                finalAudioGcsPath=narration.final_audio_gcs_path,
            )
            # Firestoreに完了ステータスと最終データを書き込み
            await update_job_status(
                self._db_client, job_id, "completed", final_data_model.model_dump()
            )

            final_message = f"ジョブ {job_id} のワークフローが正常に完了しました。"
            self._logger.info(
                f"[{job_id}] {final_message} 結果をFirestoreに書き込みました。"
            )

            # 最終的な成功メッセージをイベントとして返す
            yield Event(
                author=self.name, content=Content(parts=[Part(text=final_message)])
            )

        except Exception as e:
            self._logger.error(
                f"[{job_id}] Firestoreへの結果書き込み中にエラーが発生しました: {e}",
                exc_info=True,
            )
            await update_job_status(
                self._db_client,
                job_id,
                "error",
                {"errorMessage": f"最終結果の処理に失敗しました: {e}"},
            )
            raise