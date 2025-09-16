# 各種エージェント

from functools import lru_cache

from agents.explainer_agent.agent import ExplainerAgent
from agents.illustrator_agent.agent import IllustratorAgent
from agents.narrator_agent.agent import NarratorAgent
from agents.result_writer_agent.agent import ResultWriterAgent
from agents.transcriber_agent.agent import TranscriberAgent
from callback import after_agent_callback, before_agent_callback

# FastAPI & CloudEvents
from cloudevents.http import from_http
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)

# ADK & GenAI SDK
from google.adk.agents import ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService
from google.cloud import firestore
from google.genai.types import Content, Part

# モデル、サービス、コールバック関数
from models.agent_models import StorageObjectData
from pydantic import ValidationError
from services.firestore_service import update_job_status
from services.logging_service import get_logger, setup_logging
from services.session_service import create_session_service

# 設定
from config import get_settings

app = FastAPI()

APP_NAME = "coco-ai"  # A logical name for the application/agent.

# ---------------------------
# ログと設定の初期化
# ---------------------------
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


# ---------------------------
# 依存性注入用の関数
# ---------------------------
@lru_cache
def get_session_service() -> BaseSessionService:
    """セッションサービスのシングルトンインスタンスを生成・取得する。"""
    return create_session_service()


@lru_cache
def get_firestore_client() -> firestore.Client:
    """Firestore Clientのシングルトンインスタンスを生成・取得する。"""
    return firestore.Client()


# ---------------------------
# ヘルパー関数
# ---------------------------
async def _parse_cloudevent_payload(request: Request) -> dict:
    """
    FastAPIリクエストからCloudEventペイロードを解析・検証する。

    job_id, user_id, bucket, object名を抽出し、
    イベントが期待されるバケットから来たものであることを確認するセキュリティチェックも行う。
    """
    try:
        headers = request.headers
        body = await request.body()
        event = from_http(headers, body)
        if not event.data:
            raise ValueError("CloudEventのデータが空です。")

        # Pydanticモデルを使用してペイロードを検証・解析
        storage_data = StorageObjectData.model_validate(event.data)

        # イベントペイロードからデータを抽出
        job_id = storage_data.metadata.job_id
        user_id = storage_data.metadata.user_id
        bucket = storage_data.bucket
        name = storage_data.name

        # セキュリティチェック: イベントが期待されたバケットからのものか確認
        if bucket != settings.audio_upload_bucket:
            logger.error(
                f"[{job_id}] 不正なバケットです: {bucket}。期待されるバケット: {settings.audio_upload_bucket}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="予期しないソースバケットからのイベントです。",
            )
        return {"job_id": job_id, "user_id": user_id, "bucket": bucket, "name": name}
    except ValidationError as e:
        logger.error(f"不正なCloudEventペイロードです: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"不正なペイロードです: {e}"
        )
    except Exception as e:
        logger.error(f"CloudEventの解析に失敗しました: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CloudEventを解析できませんでした。",
        )


# ---------------------------------
# ルートエージェントの構築
# ---------------------------------
def build_root_agent() -> SequentialAgent:
    """
    エージェントの処理パイプラインを構築する。

    処理フロー:
      音声文字起こし (Transcriber)
      -> 子供向け解説生成 (Explainer)
      -> [並列処理]
         - イラスト生成 (Illustrator)
         - 音声合成 (Narrator)
      -> 最終結果の書き込み (ResultWriter)

    IllustratorとNarratorは `ParallelAgent` を使って並列実行される。
    最終的な失敗チェックは `ResultWriterAgent` で行われる。
    """
    transcriber = TranscriberAgent()
    explainer = ExplainerAgent()
    illustrator = IllustratorAgent()
    narrator = NarratorAgent()
    result_writer = ResultWriterAgent()

    # イラスト生成と音声合成を並列実行するブランチ
    parallel_branch = ParallelAgent(
        name="IllustrateAndNarrate",
        sub_agents=[illustrator, narrator],
        description="イラスト生成と音声合成を並列で実行します。",
    )

    # 全体の処理を定義するシーケンシャルなエージェント
    root = SequentialAgent(
        name="CocoAIPipeline",
        sub_agents=[transcriber, explainer, parallel_branch, result_writer],
        before_agent_callback=before_agent_callback,
        after_agent_callback=after_agent_callback,
    )
    return root


async def run_pipeline_in_background(
    event_data: dict,
    session_service: BaseSessionService,
    db_client: firestore.Client,
):
    """
    バックグラウンドで実行されるエージェントパイプラインのメインロジック。
    """
    job_id = event_data["job_id"]
    user_id = event_data["user_id"]
    bucket = event_data["bucket"]
    name = event_data["name"]

    gcs_uri = f"gs://{bucket}/{name}"
    logger.info(f"[{job_id}] CloudEventを受信しました: {gcs_uri}")
    try:
        # セッションの初期状態を設定
        initial_state = {"job_id": job_id, "gcs_uri": gcs_uri}
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=job_id
        )
        if not session:
            # 新しいセッションの場合、初期状態を注入してセッションを作成
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=job_id,
                state=initial_state,
            )

        # エージェントパイプラインを構築し、Runnerを初期化
        root_agent = build_root_agent()
        runner = Runner(
            agent=root_agent, app_name=APP_NAME, session_service=session_service
        )

        # エージェントへの初期入力を作成
        user_content = Content(parts=[Part(text=gcs_uri)])

        # エージェントパイプラインを実行
        final_response_content = "最終レスポンスイベントを受信しませんでした。"
        async for event in runner.run_async(
            user_id=user_id, session_id=job_id, new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_response_content = event.content.parts[0].text

        logger.info(
            f"[{job_id}] ワークフローが完了しました。最終レスポンス: {final_response_content}"
        )
    except Exception as e:
        logger.error(
            f"[{job_id}] ワークフローでエラーが発生しました: {e}", exc_info=True
        )
        # エラーが発生した場合、Firestoreのジョブステータスを更新
        try:
            await update_job_status(
                db_client, job_id, "error", {"errorMessage": str(e)}
            )
        except Exception as db_error:
            logger.error(
                f"[{job_id}] Firestoreへのエラー状態の書き込みに失敗しました: {db_error}"
            )


# ---------------------------------
# Eventarcトリガーのエンドポイント
# ---------------------------------
@app.post("/invoke")
async def invoke_pipeline(
    request: Request,
    background_tasks: BackgroundTasks,
    session_service: BaseSessionService = Depends(get_session_service),
    db_client: firestore.Client = Depends(get_firestore_client),
):
    """
    Cloud StorageへのファイルアップロードをトリガーにEventarcから呼び出されるメインエンドポイント。
    リクエストを即座にACKし、重い処理はバックグラウンドで実行する。
    """
    # CloudEventペイロードを解析・検証
    # ヘルパー関数内で発生したHTTPExceptionはFastAPIによって自動的に伝播される
    event_data = await _parse_cloudevent_payload(request)

    # バックグラウンドでパイプライン処理を実行するようにスケジュール
    # 依存性注入されたsession_serviceインスタンスをタスクに渡す
    # FastAPIは非同期関数を直接扱えるため、ラッパーは不要
    background_tasks.add_task(
        run_pipeline_in_background, event_data, session_service, db_client
    )

    # Eventarcに即座に成功応答（204 No Content）を返し、リトライを防ぐ
    return Response(status_code=status.HTTP_204_NO_CONTENT)
