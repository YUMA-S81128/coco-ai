from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from models.agent_models import ExplanationOutput


class BaseProcessingAgent(BaseAgent):
    """
    解説データ（ExplanationOutput）を処理するエージェントのベースクラス。

    セッション状態から必要なデータ（job_id, explanation_data）を抽出し、
    検証するための共通メソッドを提供する。これにより、サブクラスでの定型コードを削減する。
    """

    def _get_common_data(
        self, context: InvocationContext
    ) -> tuple[str, ExplanationOutput]:
        """
        セッション状態から job_id と explanation_data を取得し、検証する。

        Args:
            context: セッション状態を含む呼び出しコンテキスト。

        Returns:
            job_id（文字列）とパースされたExplanationOutputモデルを含むタプル。

        Raises:
            ValueError: job_id または explanation_data がセッション状態にない場合。
        """
        job_id = context.session.state.get("job_id")
        explanation_data = context.session.state.get("explanation_data")

        if not job_id or not explanation_data:
            raise ValueError(
                "job_id と explanation_data がセッション状態に存在する必要があります。"
            )

        explanation = ExplanationOutput.model_validate(explanation_data)
        return job_id, explanation
