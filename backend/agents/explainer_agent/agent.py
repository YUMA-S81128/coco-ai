from google.adk.agents import LlmAgent
from models.agent_models import ExplanationOutput
from services.logging_service import get_logger

from .config import GENERATE_CONFIG, MODEL_ID
from .prompt import SYSTEM_INSTRUCTION_PROMPT


class ExplainerAgent(LlmAgent):
    """
    子供の年齢に合わせた回答、イラスト指示、親向けヒントを生成する
    対話・解説エージェント。
    """

    def __init__(self):
        super().__init__(
            name="ExplainerAgent",
            description="未就学児向けの質問にやさしく回答する対話・解説エージェント",
            model=MODEL_ID,
            generate_content_config=GENERATE_CONFIG,
            instruction=SYSTEM_INSTRUCTION_PROMPT,
            output_key="explanation_data",
            output_schema=ExplanationOutput,
        )
        self.logger = get_logger(__name__)
