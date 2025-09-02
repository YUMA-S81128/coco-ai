from google.adk.agents.callback_context import CallbackContext
from services.firestore_service import update_job_status
from services.logging_service import get_logger

logger = get_logger(__name__)

AGENT_STATUS_MAP = {
    "TranscriberAgent": "transcribing",
    "ExplainerAgent": "explaining",
    "IllustratorAgent": "illustrating",
    "NarratorAgent": "narrating",
    "ResultWriterAgent": "finishing",
}

PARALLEL_AGENTS = {
    "IllustrateAndNarrate": {
        "illustration": {"ok_key": "illustration", "err_key": "illustration_error"},
        "narration": {"ok_key": "narration", "err_key": "narration_error"},
    }
}


# ---------------------------
# Before Agent Callback
# ---------------------------
async def before_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    Called before each agent runs.
    - Logs entry.
    - Updates Firestore progress (best-effort).
    """
    agent_name = getattr(callback_context, "agent_name", None)
    state_obj = getattr(callback_context, "state", None)

    # state を dict に変換
    state = state_obj.to_dict() if state_obj else {}

    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id or 'unknown'}] Entering agent: {agent_name}")

    if agent_name and job_id:
        status = AGENT_STATUS_MAP.get(agent_name)
        if status:
            try:
                await update_job_status(job_id, status)
            except Exception as e:
                logger.warning(f"[{job_id}] Failed to update status '{status}': {e}")

    return None


# ---------------------------
# After Agent Callback
# ---------------------------
async def after_agent_callback(
    callback_context: CallbackContext,
) -> None:
    agent_name = getattr(callback_context, "agent_name", "unknown")
    state_obj = getattr(callback_context, "state", None)

    # state を dict に変換
    state = state_obj.to_dict() if state_obj else {}

    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] after_agent_callback: agent {agent_name} exited")

    # ParallelAgent ハンドリング
    if agent_name in PARALLEL_AGENTS:
        errors = {}
        for label, keys in PARALLEL_AGENTS[agent_name].items():
            ok_val = state.get(keys["ok_key"])
            err_val = state.get(keys["err_key"])
            if err_val:
                logger.error(
                    f"[{job_id}] Parallel sub-agent '{label}' failed: {err_val}"
                )
                errors[label] = str(err_val)
            elif not ok_val:
                logger.warning(
                    f"[{job_id}] Parallel sub-agent '{label}' missing success key '{keys['ok_key']}'"
                )
                errors[label] = "missing_result"
            else:
                logger.info(f"[{job_id}] Parallel sub-agent '{label}' succeeded")

        if errors:
            if state_obj:
                try:
                    state_obj["parallel_errors"] = errors
                    state_obj["workflow_failed"] = True
                except Exception:
                    logger.warning(
                        f"[{job_id}] Could not write parallel_errors to callback state"
                    )
            logger.warning(
                f"[{job_id}] ParallelAgent '{agent_name}' aggregated errors: {list(errors.keys())}"
            )
        else:
            if state_obj:
                state_obj["parallel_ok"] = True

        return None

    # 単一エージェント用ログ（ok / err キーがあれば）
    SINGLE_AGENT_KEYS = {
        "TranscriberAgent": ("transcription", "transcription_error"),
        "ExplainerAgent": ("explanation_data", "explanation_error"),
        "IllustratorAgent": ("illustration", "illustration_error"),
        "NarratorAgent": ("narration", "narration_error"),
        "ResultWriterAgent": (None, None),
    }

    if agent_name in SINGLE_AGENT_KEYS:
        ok_key, err_key = SINGLE_AGENT_KEYS[agent_name]
        if err_key and state.get(err_key):
            logger.error(
                f"[{job_id}] Agent '{agent_name}' failed: {state.get(err_key)}"
            )
            if state_obj:
                state_obj["workflow_failed"] = True
        else:
            logger.info(
                f"[{job_id}] Agent '{agent_name}' completed (ok_key='{ok_key}')"
            )
        return None

    # --- Fallback ---
    logger.info(
        f"[{job_id}] after_agent_callback: no special handling for agent '{agent_name}'"
    )
    return None
