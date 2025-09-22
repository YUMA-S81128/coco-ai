from google.adk.agents.callback_context import CallbackContext
from services.logging_service import get_logger

logger = get_logger(__name__)


# --------------------------------------
# エージェント実行前のコールバック
# --------------------------------------
async def before_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    エージェントの実行が開始される前に呼び出され、エージェントの実行開始をログに記録する。
    """
    agent_name = getattr(callback_context, "agent_name", None)
    state_obj = getattr(callback_context, "state", None)

    # stateオブジェクトを辞書に変換する。
    state = state_obj.to_dict() if state_obj else {}

    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] エージェント '{agent_name}' を開始します。")

    return None


# --------------------------------------
# エージェント実行後のコールバック
# --------------------------------------
async def after_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    エージェントが終了した後に呼び出され、エージェントの実行終了をログに記録する。
    """
    agent_name = getattr(callback_context, "agent_name", "unknown")
    state_obj = getattr(callback_context, "state", None)

    # stateオブジェクトを辞書に変換する。
    state = state_obj.to_dict() if state_obj else {}

    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] エージェント '{agent_name}' を終了します。")

    return None
