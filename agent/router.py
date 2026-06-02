import logging
from .state import AgentState

logger = logging.getLogger(__name__)

def route_intent(state: AgentState):
    """Determines whether to query metadata and generate SQL or skip directly to synthesis."""
    intent = state.get("intent", "chat")
    requires_clarification = state.get("requires_clarification", False)
    
    # Route to database querying nodes only for valid, unambiguous business queries
    if intent in ["business_query", "followup_business_query"] and not requires_clarification:
        return "metadata_pruner_node"
    return "insight_synthesis_node"


def route_execution(state: AgentState):
    """Determines whether to retry SQL generation or proceed to synthesis based on state."""
    if state["sql_results"] is not None:
        return "insight_synthesis_node"
        
    if state.get("error_logs"):
        last_error = state["error_logs"][-1]["error"]
        if "Security Violation" in last_error:
            return "insight_synthesis_node"
            
        if state.get("attempt_count", 0) < 3:
            logger.info(f"Self-Healing: Rerouting failed execution (attempt {state['attempt_count']}) back to Generator...")
            return "sql_generation_node"
            
    return "insight_synthesis_node"
