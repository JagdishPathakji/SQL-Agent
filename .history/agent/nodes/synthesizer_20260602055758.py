import json
from typing import Dict, Any
from ..state import AgentState

def insight_synthesis_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Synthesizing analysis results..."]
    llm = state["llm_client"]
    privacy = state["privacy_level"]
    user_query = state["user_query"]
    sql = state["generated_sql"]
    
    # If conversational mode was triggered, skip SQL result processing
    if not state.get("is_db_query", True):
        steps.append("Workflow completed successfully (Conversational).")
        return {
            "steps_log": steps
        }
        
    # Check if there are no query results due to security abort or uncorrected error
    if state["sql_results"] is None:
        last_error = state["error_logs"][-1]["error"] if state["error_logs"] else "Unknown execution error."
        insight = f"Unable to answer the question due to database execution failure:\n\n`{last_error}`"
        steps.append("Workflow completed with errors.")
        return {
            "compiled_natural_insight": insight,
            "steps_log": steps
        }
        
    results_json = json.dumps(state["sql_results"][:30], default=str)  # limit to top 30 records for context
    
    if privacy == "Standard":
        # Full insight synthesis mode
        sys_prompt = (
            "You are a professional database data analyst. Synthesize a clean, clear, "
            "and concise natural business insight answering the user's question using the query "
            "results. Do not discuss technical details of the SQL syntax or query execution. "
            "Just explain the data."
        )
        user_prompt = (
            f"User Question: {user_query}\n\n"
            f"Executed SQL: {sql}\n\n"
            f"Query Results Data (Top 30 records):\n{results_json}\n\n"
            "Generate natural explanation:"
        )
    else:
        # Data Privacy modes (DDL Only or DDL + Sample Rows) - Do not send data rows to LLM
        sys_prompt = (
            "You are a database privacy compliance officer. The user has run a database query in "
            "Strict Data Privacy Mode. You cannot see the query results data. Explain what fields "
            "and information this SQL query retrieves to answer the user's question, without referring "
            "to any database content rows or results. Keep it professional and concise."
        )
        user_prompt = (
            f"User Question: {user_query}\n\n"
            f"Executed SQL: {sql}\n\n"
            "Provide the high-level compliance summary of the operation:"
        )
        
    insight = llm.generate_chat(sys_prompt, user_prompt, temperature=0.3)
    
    # Append privacy notices if privacy mode was engaged
    if privacy != "Standard":
        insight = (
            f"🔒 **Strict Privacy Mode Active**: Database records were processed locally on your machine and "
            "were not sent to the LLM.\n\n"
            f"{insight}"
        )
        
    steps.append("Workflow completed successfully.")
    
    return {
        "compiled_natural_insight": insight,
        "steps_log": steps
    }
