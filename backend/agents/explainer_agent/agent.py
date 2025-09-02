from google.adk.agents import LlmAgent
from models.agent_models import ExplanationOutput
from services.logging_service import get_logger

from .config import GENERATE_CONFIG, MODEL_ID
from .prompt import SYSTEM_INSTRUCTION_PROMPT


class ExplainerAgent(LlmAgent):
    """
    A conversational and explanatory agent that generates answers tailored for
    young children, along with illustration prompts and hints for parents.

    This agent uses a Gemini model to process the transcribed text and outputs
    a structured JSON object defined by the `ExplanationOutput` schema.
    """

    def __init__(self):
        super().__init__(
            name="ExplainerAgent",
            description="Generates child-friendly explanations, illustration prompts, and parent hints.",
            model=MODEL_ID,
            generate_content_config=GENERATE_CONFIG,
            instruction=SYSTEM_INSTRUCTION_PROMPT,
            output_key="explanation_data",
            output_schema=ExplanationOutput,
        )
        self.logger = get_logger(__name__)
