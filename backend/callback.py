from google.adk.agents.callback_context import CallbackContext
from services.firestore_service import update_job_status
from services.logging_service import get_logger

logger = get_logger(__name__)

# A mapping from agent names to human-readable status strings for Firestore.
AGENT_STATUS_MAP = {
    "TranscriberAgent": "transcribing",
    "ExplainerAgent": "explaining",
    # The ParallelAgent itself doesn't have a single status.
    # We use the sub-agent names for more granular status updates.
    "IllustratorAgent": "illustrating",
    "NarratorAgent": "narrating",
    "ResultWriterAgent": "finishing",
}


# ---------------------------
# Before Agent Callback
# ---------------------------
async def before_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    Called by the ADK runner before each agent in the sequence begins execution.

    This function logs the entry into an agent and attempts to update the job's
    status in Firestore to provide real-time progress feedback to the user.
    The Firestore update is a best-effort operation and will not halt the
    workflow if it fails.
    """
    agent_name = getattr(callback_context, "agent_name", None)
    state_obj = getattr(callback_context, "state", None)

    # Convert state object to a dictionary for easier access.
    state = state_obj.to_dict() if state_obj else {}

    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] Entering agent: {agent_name}")

    if agent_name and job_id:
        status = AGENT_STATUS_MAP.get(agent_name)
        if status:
            try:
                # Best-effort update to Firestore.
                await update_job_status(job_id, status)
            except Exception as e:
                logger.warning(
                    f"[{job_id}] Failed to update Firestore status to '{status}': {e}"
                )

    return None


# ---------------------------
# After Agent Callback
# ---------------------------
async def after_agent_callback(
    callback_context: CallbackContext,
) -> None:
    """
    Called by the ADK runner after each agent in the main sequence finishes.

    This function logs the agent's exit and performs error checking.
    - For ParallelAgent, it checks for aggregated errors from sub-agents.
    - It sets a 'workflow_failed' flag in the state if any agent fails,
      which is used by the ResultWriterAgent to determine the final job status.
    """
    agent_name = getattr(callback_context, "agent_name", "unknown")
    state_obj = getattr(callback_context, "state", None)
    state = state_obj.to_dict() if state_obj else {}
    job_id = state.get("job_id", "unknown")
    logger.info(f"[{job_id}] Exited agent: {agent_name}")

    # ADK's ParallelAgent automatically catches exceptions from its sub-agents
    # and stores them in the 'parallel_errors' key in the session state.
    if agent_name == "IllustrateAndNarrate":
        parallel_errors = state.get("parallel_errors")
        if parallel_errors:
            logger.error(
                f"[{job_id}] One or more parallel sub-agents failed: {parallel_errors}"
            )
            if state_obj:
                # This flag will be checked by the final ResultWriterAgent.
                state_obj["workflow_failed"] = True
        else:
            # Additionally, verify that the expected outputs were actually produced.
            missing_results = []
            if "illustration" not in state:
                missing_results.append("illustration")
            if "narration" not in state:
                missing_results.append("narration")

            if missing_results:
                error_msg = f"Parallel sub-agents completed but results are missing: {missing_results}"
                logger.error(f"[{job_id}] {error_msg}")
                if state_obj:
                    state_obj["workflow_failed"] = True
                    # Store this specific error information.
                    if "parallel_errors" not in state_obj:
                        state_obj["parallel_errors"] = {}
                    state_obj["parallel_errors"]["missing_results"] = error_msg
            else:
                logger.info(
                    f"[{job_id}] Parallel agent '{agent_name}' and all its sub-agents completed successfully."
                )
        return

    # For sequential agents, ADK will typically raise an exception upon failure,
    # which is caught by the main runner loop. This callback is usually only
    # called on success. However, we can check for output keys as a safeguard.
    # Note: LlmAgent might produce an '[output_key]_error' on graceful failure.
    agent_error = state.get(f"{agent_name}_error")  # For LlmAgent
    if agent_error:
        logger.error(
            f"[{job_id}] Agent '{agent_name}' failed gracefully with error: {agent_error}"
        )
        if state_obj:
            state_obj["workflow_failed"] = True
    else:
        logger.info(f"[{job_id}] Agent '{agent_name}' completed.")

    return None

    # --- Fallback ---
    logger.info(
        f"[{job_id}] after_agent_callback: no special handling for agent '{agent_name}'"
    )
    return None
