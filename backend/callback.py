from dependencies import get_firestore_client
from google.adk.agents.callback_context import CallbackContext
from pydantic import BaseModel
from services.firestore_service import update_job_data
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


async def after_explainer_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    ExplainerAgentの実行後に呼び出され、生成された解説データをFirestoreに書き込む。
    """
    state = callback_context.state.to_dict()

    job_id = state.get("job_id")
    if not job_id:
        logger.warning(
            "job_idがstateに見つからないため、コールバックをスキップします。"
        )
        return

    explanation_data = state.get("explanation_data")
    if not explanation_data:
        logger.warning(
            f"[{job_id}] stateにexplanation_dataが見つからないため、コールバックをスキップします。{state}"
        )
        return

    try:
        # Pydanticモデルを辞書に変換
        if isinstance(explanation_data, BaseModel):
            explanation_data_dict = explanation_data.model_dump(
                by_alias=True, exclude_none=True
            )
        else:
            explanation_data_dict = explanation_data

        # フロントエンドのJobモデルのキー（キャメルケース）に合わせてデータを整形
        update_data = {
            "childExplanation": explanation_data_dict.get("child_explanation"),
        }

        logger.info(f"[{job_id}] jobsコレクションに解説データを書き込みます...")
        db_client = get_firestore_client()
        await update_job_data(db=db_client, job_id=job_id, data=update_data)
        logger.info(
            f"[{job_id}] jobsコレクションへの解説データ書き込みが完了しました。"
        )
    except Exception as e:
        logger.warning(f"[{job_id}] Firestoreへの解説データ書き込みに失敗しました: {e}")
