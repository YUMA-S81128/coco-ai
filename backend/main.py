# Agents
from agents.explainer_agent.agent import ExplainerAgent
from agents.illustrator_agent.agent import IllustratorAgent
from agents.narrator_agent.agent import NarratorAgent
from agents.result_writer_agent.agent import ResultWriterAgent
from agents.transcriber_agent.agent import TranscriberAgent
from callback import after_agent_callback, before_agent_callback

# FastAPI & CloudEvents
from cloudevents.http import from_http
from fastapi import FastAPI, HTTPException, Request, status

# ADK & GenAI SDK
from google.adk.agents import ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.genai.types import Content, Part

# models & services & callback
from models.agent_models import StorageObjectData
from pydantic import ValidationError
from services.firestore_service import update_job_status
from services.logging_service import get_logger, setup_logging
from services.session_service import create_session_service

# config
from config import get_settings

app = FastAPI()

APP_NAME = "Coco-Ai"

# ---------------------------
# Logging & Settings
# ---------------------------
setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# ---------------------------
# SessionService
# ---------------------------
session_service = create_session_service()


# ---------------------------
# Build Root Agent
# ---------------------------
def build_root_agent() -> SequentialAgent:
    """
    Construct the root agent pipeline:
      Transcriber -> Explainer -> (Parallel: Illustrator & Narrator) -> ResultWriter
    This uses ParallelAgent so branches run concurrently;
    final failure-check will be performed in ResultWriterAgent
    """
    transcriber = TranscriberAgent()
    explainer = ExplainerAgent()
    illustrator = IllustratorAgent()
    narrator = NarratorAgent()
    result_writer = ResultWriterAgent()

    parallel_branch = ParallelAgent(
        name="IllustrateAndNarrate",
        sub_agents=[illustrator, narrator],
        description="Run image generation and text-to-speech concurrently",
    )

    root = SequentialAgent(
        name="CocoAIPipeline",
        sub_agents=[transcriber, explainer, parallel_branch, result_writer],
        before_agent_callback=before_agent_callback,
        after_agent_callback=after_agent_callback,
    )
    return root


# ---------------------------
# Eventarc Handler
# ---------------------------
@app.post("/invoke")
async def invoke_pipeline(request: Request):
    # 1. リクエストの検証とデータ抽出
    try:
        headers = request.headers
        body = await request.body()
        event = from_http(headers, body)
        if not event.data:
            raise ValueError("CloudEvent data is empty.")

        # Pydanticモデルでペイロードを検証・パース
        storage_data = StorageObjectData.model_validate(event.data)

        job_id = storage_data.metadata.jobId
        user_id = storage_data.metadata.userId
        bucket = storage_data.bucket
        name = storage_data.name

    except ValidationError as e:
        logger.error(f"Invalid CloudEvent payload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid payload: {e}"
        )
    except Exception as e:
        logger.error(f"Failed to parse CloudEvent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse CloudEvent.",
        )

    gcs_uri = f"gs://{bucket}/{name}"
    logger.info(f"[{job_id}] Received CloudEvent for {gcs_uri}")

    try:
        initial_state = {"job_id": job_id, "gcs_uri": gcs_uri}
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=job_id
        )
        if not session:
            # 新規の場合は初期stateを注入
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=job_id,
                state=initial_state,
            )

        root_agent = build_root_agent()
        runner = Runner(
            agent=root_agent, app_name=APP_NAME, session_service=session_service
        )

        user_content = Content(parts=[Part(text=gcs_uri)])

        # エージェントの実行
        async for event in runner.run_async(
            user_id=user_id, session_id=job_id, new_message=user_content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_response_content = event.content.parts[0].text

        logger.info(
            f"[{job_id}] Workflow completed. Final response: {final_response_content}"
        )
        await update_job_status(job_id, "completed")
    except Exception as e:
        logger.error(f"[{job_id}] Workflow failed: {e}", exc_info=True)
        await update_job_status(job_id, "failed", {"errors": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
