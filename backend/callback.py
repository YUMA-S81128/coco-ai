# ADKコールバックはFastAPIのDIシステムの外で実行されるため、
# 必要な依存関係をここで直接取得します。
# lru_cacheパターンを使用することで、
# パイプライン実行中にインスタンスが再生成されるのを防ぎます。
from typing import Any, Callable, Dict, Optional

from dependencies import get_firestore_client
from google.adk.agents.callback_context import CallbackContext
from services.firestore_service import update_job_status
from services.logging_service import get_logger

logger = get_logger(__name__)

# エージェント名をFirestoreに保存するステータス文字列にマッピング
AGENT_STATUS_MAP: Dict[str, str] = {
    "TranscriberAgent": "transcribing",
    "ExplainerAgent": "explaining",
    "IllustratorAgent": "illustrating",
    "NarratorAgent": "narrating",
    "ResultWriterAgent": "finishing",
}


def _get_transcriber_payload(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """TranscriberAgentの状態からFirestoreペイロードを生成する。"""
    if "transcription" in state and state["transcription"].get("text"):
        return {"transcribedText": state["transcription"]["text"]}
    return None


def _get_explainer_payload(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """ExplainerAgentの状態からFirestoreペイロードを生成する。"""
    if "explanation_data" in state:
        exp_data = state["explanation_data"]
        return {
            "childExplanation": exp_data.get("child_explanation"),
            "parentHint": exp_data.get("parent_hint"),
            "illustrationPrompt": exp_data.get("illustration_prompt"),
        }
    return None


# エージェント名とペイロード生成ハンドラの対応辞書
PAYLOAD_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = {
    "TranscriberAgent": _get_transcriber_payload,
    "ExplainerAgent": _get_explainer_payload,
}


# --------------------------------------
# エージェント実行前のコールバック
# --------------------------------------
async def before_agent_callback(callback_context: CallbackContext) -> None:
    """
    シーケンス内の各エージェントが実行を開始する前にADKランナーによって呼び出される。
    この関数は、エージェントへのエントリーをログに記録する。
    """
    agent_name = getattr(callback_context, "agent_name", "unknown")
    state = getattr(callback_context, "state", {})
    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] Starting agent: {agent_name}")


# --------------------------------------
# エージェント実行後のコールバック
# --------------------------------------
async def after_agent_callback(callback_context: CallbackContext) -> None:
    """
    メインシーケンスの各エージェントが終了した後にADKランナーによって呼び出される。
    この関数は、エージェントの終了をログに記録し、中間結果をFirestoreに書き込み、
    エラーチェックを実行する。
    """
    agent_name = getattr(callback_context, "agent_name", "unknown")
    state_obj = getattr(callback_context, "state", None)
    state = state_obj.to_dict() if state_obj else {}
    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] Finished agent: {agent_name}")

    db_client = get_firestore_client()

    try:
        # --- 1. シーケンシャルエージェントの中間結果を書き込む ---
        handler = PAYLOAD_HANDLERS.get(agent_name)
        if handler:
            data_payload = handler(state)
            status = AGENT_STATUS_MAP.get(agent_name)
            if data_payload and status:
                await update_job_status(db_client, job_id, status, data_payload)

        # --- 2. ParallelAgentのサブエージェントの結果を個別に書き込む ---
        if agent_name == "IllustrateAndNarrate":
            # IllustratorAgentの結果
            if "illustration" in state:
                image_path = state["illustration"].get("image_gcs_path")
                illustrator_status = AGENT_STATUS_MAP.get("IllustratorAgent")
                if image_path and illustrator_status:
                    await update_job_status(
                        db_client,
                        job_id,
                        illustrator_status,
                        {"imageGcsPath": image_path},
                    )
            # NarratorAgentの結果
            if "narration" in state:
                audio_path = state["narration"].get("final_audio_gcs_path")
                narrator_status = AGENT_STATUS_MAP.get("NarratorAgent")
                if audio_path and narrator_status:
                    await update_job_status(
                        db_client,
                        job_id,
                        narrator_status,
                        {"finalAudioGcsPath": audio_path},
                    )

    except Exception as e:
        logger.warning(
            f"[{job_id}] Failed to write intermediate results for {agent_name}: {e}",
            exc_info=True,
        )

    # --- 3. ワークフローのエラーチェック（変更なし） ---
    if agent_name == "IllustrateAndNarrate":
        parallel_errors = state.get("parallel_errors")
        if parallel_errors:
            logger.error(
                f"[{job_id}] One or more parallel sub-agents failed: {parallel_errors}"
            )
            if state_obj:
                state_obj["workflow_failed"] = True
        else:
            missing_results = []
            if "illustration" not in state:
                missing_results.append("illustration")
            if "narration" not in state:
                missing_results.append("narration")

            if missing_results:
                error_msg = f"Parallel sub-agents completed but results are missing: {missing_results}"
                logger.error(f"[{job_id}] {error_msg}")
                if state_obj:
                    state_obj["workflow_failed"] = True
                    if "parallel_errors" not in state_obj:
                        state_obj["parallel_errors"] = {}
                    state_obj["parallel_errors"]["missing_results"] = error_msg
            else:
                logger.info(
                    f"[{job_id}] Parallel agent '{agent_name}' and all its sub-agents completed successfully."
                )
        return

    agent_error = state.get(f"{agent_name}_error")

    if agent_error:
        logger.error(
            f"[{job_id}] Agent '{agent_name}' failed gracefully with error: {agent_error}"
        )
        if state_obj:
            state_obj["workflow_failed"] = True
