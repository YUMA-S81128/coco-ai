from dependencies import get_firestore_client
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from models.agent_models import ExplanationOutput
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


# --------------------------------------
# TranscriberAgent実行後のコールバック
# --------------------------------------
async def after_transcriber_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    TranscriberAgentの実行後に呼び出され、音声の文字起こしデータをFirestoreに書き込む。
    """
    state = callback_context.state.to_dict()

    logger.info(f"[callback] state: {state}")

    job_id = state.get("job_id")
    if not job_id:
        logger.warning(
            "job_idがstateに見つからないため、エージェントコールバックをスキップします。"
        )
        return

    transcribed_text = state.get("transcribed_text")
    if not transcribed_text:
        logger.warning(
            f"[{job_id}] stateにtranscribed_textが見つからないため、エージェントコールバックをスキップします。"
        )
        return

    try:
        logger.info(
            f"[{job_id}] jobsコレクションに音声の文字起こしデータを書き込みます..."
        )
        db_client = get_firestore_client()
        await update_job_data(
            db=db_client, job_id=job_id, data={"transcribedText": transcribed_text}
        )
        logger.info(
            f"[{job_id}] jobsコレクションへの音声の文字起こしデータ書き込みが完了しました。"
        )
    except Exception as e:
        logger.warning(
            f"[{job_id}] Firestoreへの音声の文字起こしデータ書き込みに失敗しました: {e}"
        )


# --------------------------------------
# ExplainerAgent実行後のコールバック
# --------------------------------------
async def parse_and_store_llm_response_as_explanation(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> None:
    """
    LLMからのレスポンスをパースし、ExplanationOutputとしてstateに格納する。
    after_model_callbackとして使用する。
    パースに失敗しても後続の処理は続行される。
    """

    state = callback_context.state
    job_id = state.get("job_id", "unknown")

    if not (llm_response.content and llm_response.content.parts):
        logger.warning(
            f"[{job_id}] LLMからのレスポンスにコンテンツが含まれていないため、モデルコールバックをスキップします。"
        )
        return

    if len(llm_response.content.parts) == 0 or not (llm_response.content.parts[0].text):
        logger.warning(
            f"[{job_id}] LLMからのレスポンスにテキストコンテンツが含まれていないため、モデルコールバックをスキップします。"
        )
        return

    json_str = llm_response.content.parts[0].text

    try:
        # JSON文字列を直接Pydanticモデルに変換
        parsed_output = ExplanationOutput.model_validate_json(json_str)

        # パースしたデータをstateに格納
        state["explanation_data"] = parsed_output
        logger.info(f"[{job_id}] 'explanation_data' をstateに正常に格納しました。")

    except Exception as e:
        # パースに失敗しても処理を止めず、警告ログのみ出力する
        logger.warning(
            f"[{job_id}] LLM出力のパースとstateへの格納に失敗しました。後続の処理は継続します。エラー: {e}",
            exc_info=True,
        )

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
            "job_idがstateに見つからないため、エージェントコールバックをスキップします。"
        )
        return

    explanation_data = state.get("explanation_data")
    if not explanation_data:
        logger.warning(
            f"[{job_id}] stateにexplanation_dataが見つからないため、エージェントコールバックをスキップします。"
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
