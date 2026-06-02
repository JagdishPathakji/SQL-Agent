from langgraph.graph import StateGraph, END
from .state import AgentState
from .router import route_intent, route_execution
from .nodes import (
    intent_classifier_node,
    metadata_pruner_node,
    sql_generation_node,
    security_and_execution_node,
    insight_synthesis_node
)

def build_workflow_graph() -> StateGraph:
    """Compiles the LangGraph workflow structure."""
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("intent_classifier_node", intent_classifier_node)
    workflow.add_node("metadata_pruner_node", metadata_pruner_node)
    workflow.add_node("sql_generation_node", sql_generation_node)
    workflow.add_node("security_and_execution_node", security_and_execution_node)
    workflow.add_node("insight_synthesis_node", insight_synthesis_node)
    
    # Define Core Edges
    workflow.set_entry_point("intent_classifier_node")
    
    # Intent classification routing
    workflow.add_conditional_edges(
        "intent_classifier_node",
        route_intent,
        {
            "metadata_pruner_node": "metadata_pruner_node",
            "insight_synthesis_node": "insight_synthesis_node"
        }
    )
    
    workflow.add_edge("metadata_pruner_node", "sql_generation_node")
    workflow.add_edge("sql_generation_node", "security_and_execution_node")
    
    # Define Conditional Edge (Self-Healing Loop)
    workflow.add_conditional_edges(
        "security_and_execution_node",
        route_execution,
        {
            "sql_generation_node": "sql_generation_node",
            "insight_synthesis_node": "insight_synthesis_node"
        }
    )
    
    workflow.add_edge("insight_synthesis_node", END)
    
    return workflow.compile()