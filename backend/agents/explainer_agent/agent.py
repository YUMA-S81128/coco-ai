from google.adk.agents import LlmAgent
from models.agent_models import ExplanationOutput
from services.logging_service import get_logger

from .config import GENERATE_CONFIG, MODEL_ID
from .prompt import SYSTEM_INSTRUCTION_PROMPT


class ExplainerAgent(LlmAgent):
    """
    幼い子供向けにカスタマイズされた回答、イラストのプロンプト、
    そして親向けのヒントを生成する、対話的で説明的なエージェント。

    このエージェントはGeminiモデルを使用して、書き起こされたテキストを処理し、
    `ExplanationOutput`スキーマで定義された構造化JSONオブジェクトを出力する。
    """

    def __init__(self):
        super().__init__(
            name="ExplainerAgent",
            description="子供向けの解説、イラストプロンプト、親向けのヒントを生成します。",
            model=MODEL_ID,
            generate_content_config=GENERATE_CONFIG,
            instruction=SYSTEM_INSTRUCTION_PROMPT,
            output_key="explanation_data",  # セッションに保存する際のキー
            output_schema=ExplanationOutput,  # 出力の型定義
            disallow_transfer_to_parent=True,  # 警告を解消するため、データ転送を明示的に無効化
            disallow_transfer_to_peers=True,  # 警告を解消するため、データ転送を明示的に無効化
        )
        self._logger = get_logger(__name__)
