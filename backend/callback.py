# ADKコールバックはFastAPIのDIシステムの外で実行されるため、
# 必要な依存関係をここで直接取得します。
# lru_cacheパターンを使用することで、
# パイプライン実行中にインスタンスが再生成されるのを防ぎます。
from dependencies import get_firestore_client
from google.adk.agents.callback_context import CallbackContext
from pydantic import BaseModel
from services.firestore_service import update_job_data, update_job_status
from services.logging_service import get_logger

logger = get_logger(__name__)

# エージェント名をFirestoreに保存するステータス文字列にマッピング
AGENT_STATUS_MAP = {
    "TranscriberAgent": "transcribing",
    "ExplainerAgent": "explaining",
    # ParallelAgent自体には単一のステータスがないので、
    # より詳細なステータス更新のためにサブエージェント名を使用する
    "IllustratorAgent": "illustrating",
    "NarratorAgent": "narrating",
    "ResultWriterAgent": "finishing",
}


# --------------------------------------
# エージェント実行前のコールバック
# --------------------------------------
async def before_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    シーケンス内の各エージェントが実行を開始する前にADKランナーによって呼び出される。

    この関数は、エージェントへのエントリーをログに記録し、Firestoreのジョブステータスを
    更新しようと試みる。これにより、ユーザーにリアルタイムの進捗フィードバックを提供する。
    Firestoreの更新はベストエフォート型の操作であり、失敗してもワークフローは停止しない。
    """
    agent_name = getattr(callback_context, "agent_name", None)
    state_obj = getattr(callback_context, "state", None)

    # stateオブジェクトを辞書に変換する。
    state = state_obj.to_dict() if state_obj else {}

    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] エージェントを開始する: {agent_name}")

    if agent_name and job_id:
        status = AGENT_STATUS_MAP.get(agent_name)
        if status:
            try:
                # Firestoreへのベストエフォート更新
                db_client = get_firestore_client()
                await update_job_status(db_client, job_id, status)
            except Exception as e:
                logger.warning(
                    f"[{job_id}] Firestoreステータスを'{status}'に更新できませんでした: {e}"
                )

    return None


# --------------------------------------
# エージェント実行後のコールバック
# --------------------------------------
async def after_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    メインシーケンスの各エージェントが終了した後にADKランナーによって呼び出される。

    この関数は、エージェントの終了をログに記録し、エラーチェックを実行する。
    - ExplainerAgentの場合、結果をjobsコレクションに書き込む。
    - ParallelAgentの場合、サブエージェントからの集約されたエラーをチェックする。
    - いずれかのエージェントが失敗した場合、stateに'workflow_failed'フラグを設定する。
    """
    agent_name = getattr(callback_context, "agent_name", "unknown")
    state_obj = getattr(callback_context, "state", None)
    state = state_obj.to_dict() if state_obj else {}
    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] エージェントを終了します: {agent_name}")

    # ExplainerAgentが完了したら、その結果をjobsコレクションに書き込む
    if agent_name == "ExplainerAgent":
        explanation_data = state.get("explanation_data")
        if explanation_data and job_id:
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
                await update_job_data(
                    db=db_client, job_id=job_id, data=update_data
                )
                logger.info(f"[{job_id}] jobsコレクションへの解説データ書き込みが完了しました。")
            except Exception as e:
                logger.warning(
                    f"[{job_id}] Firestoreへの解説データ書き込みに失敗しました: {e}"
                )

    # ADKのParallelAgentは、サブエージェントからの例外を自動的にキャッチし、
    # セッションステートの'parallel_errors'キーに保存します。
    if agent_name == "IllustrateAndNarrate":
        parallel_errors = state.get("parallel_errors")
        if parallel_errors:
            logger.error(
                f"[{job_id}] 1つ以上の並列サブエージェントが失敗しました: {parallel_errors}"
            )
            if state_obj:
                # このフラグは最終的なResultWriterAgentによってチェックされる。
                state_obj["workflow_failed"] = True
        else:
            # さらに、期待される出力が実際に生成されたことを確認する。
            missing_results = []
            if "illustration" not in state:
                missing_results.append("illustration")
            if "narration" not in state:
                missing_results.append("narration")

            if missing_results:
                error_msg = f"並列サブエージェントは完了しましたが、結果がありません: {missing_results}"
                logger.error(f"[{job_id}] {error_msg}")
                if state_obj:
                    state_obj["workflow_failed"] = True
                    # この特定のエラー情報を保存する。
                    if "parallel_errors" not in state_obj:
                        state_obj["parallel_errors"] = {}
                    state_obj["parallel_errors"]["missing_results"] = error_msg
            else:
                logger.info(
                    f"[{job_id}] 並列エージェント'{agent_name}'とそのすべてのサブエージェントが正常に完了しました。"
                )
        return

    # シーケンシャルエージェントの場合、ADKは通常、失敗時に例外を発生させ、
    # それはメインのランナーループによってキャッチされます。このコールバックは通常、成功時にのみ呼び出される。
    # ただし、セーフガードとして出力キーをチェックできる。
    agent_error = state.get(f"{agent_name}_error")  # LlmAgent用
    if agent_error:
        logger.error(
            f"[{job_id}] エージェント'{agent_name}'がエラーで正常に失敗しました: {agent_error}"
        )
        if state_obj:
            state_obj["workflow_failed"] = True
    else:
        logger.info(f"[{job_id}] エージェント'{agent_name}'が完了しました。")

    return None
