from google.adk.sessions import InMemorySessionService, VertexAiSessionService

from config import get_settings
from services.logging_service import get_logger

settings = get_settings()
logger = get_logger(__name__)


# ---------------------------
# SessionService factory
# ---------------------------
def create_session_service():
    session_type_setting = settings.session_service

    if session_type_setting == "inmemory":
        logger.info("Using InMemorySessionService for ADK sessions (dev).")
        return InMemorySessionService()

    logger.info("Using VertexAiSessionService for ADK sessions (production).")
    return VertexAiSessionService(
        project=settings.google_cloud_project_id, location=settings.region
    )
