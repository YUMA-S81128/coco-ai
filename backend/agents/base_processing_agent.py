from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from models.agent_models import ExplanationOutput


class BaseProcessingAgent(BaseAgent):
    """
    A base agent for agents that process the explanation data.

    Provides a common method to extract and validate required data
    (job_id, explanation_data) from the session state. This reduces
    boilerplate code in subclasses.
    """

    def _get_common_data(
        self, context: InvocationContext
    ) -> tuple[str, ExplanationOutput]:
        """
        Retrieves and validates job_id and explanation_data from the session state.

        Args:
            context: The invocation context containing the session state.

        Returns:
            A tuple containing the job_id (str) and the parsed ExplanationOutput model.

        Raises:
            ValueError: If job_id or explanation_data is missing from the session state.
        """
        job_id = context.session.state.get("job_id")
        explanation_data = context.session.state.get("explanation_data")

        if not job_id or not explanation_data:
            raise ValueError("job_id and explanation_data must be in session state.")

        explanation = ExplanationOutput.model_validate(explanation_data)
        return job_id, explanation
