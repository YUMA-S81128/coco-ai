from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from models.agent_models import ExplanationOutput


class BaseProcessingAgent(BaseAgent):
    """
    解説データ（ExplanationOutput）を処理するエージェントのベースクラス。

    セッション状態から必要なデータ（job_id, explanation_data）を抽出し、
    検証するための共通メソッドを提供する。これにより、サブクラスでの定型コードを削減する。
    """

    async def _get_common_data(
        self, context: InvocationContext
    ) -> tuple[str, ExplanationOutput]:
        """
        セッション状態から job_id と explanation_data を取得し、検証する。
        ParallelAgent 内で実行される場合、最新のセッション状態を再取得する必要がある。

        Args:
            context: セッション状態を含む呼び出しコンテキスト。

        Returns:
            job_id（文字列）とパースされたExplanationOutputモデルを含むタプル。

        Raises:
            ValueError: job_id または explanation_data がセッション状態にない場合。
        """
        # ParallelAgentは最新のセッション状態を自動的に伝播しないため、
        # contextから直接session_serviceを取得し、手動で最新のセッションを読み込む。
        session_service = context.session_service
        session = await session_service.get_session(
            app_name=context.session.app_name,
            user_id=context.session.user_id,
            session_id=context.session.id,
        )
        state = session.state if session else {}

        job_id = state.get("job_id")
        explanation_data = state.get("explanation_data")

        if not job_id or not explanation_data:
            raise ValueError(
                "job_id と explanation_data がセッション状態に存在する必要があります。"
            )

        explanation = ExplanationOutput.model_validate(explanation_data)
        return job_id, explanation
