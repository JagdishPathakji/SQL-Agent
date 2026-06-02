import json
import re
from typing import Dict, Any
from ..state import AgentState

def recommend_chart(user_query: str, sql: str, df_columns: list, sample_data_json: str, llm) -> Dict[str, Any]:
    sys_prompt = (
        "You are a database visualization expert. Analyze the user query, SQL query, column list, and sample data to determine if a chart/graph can represent the results. "
        "Allowed chart types: 'bar', 'line', 'scatter', 'pie', 'histogram', 'none'.\n\n"
        "Rules:\n"
        "1. Recommend 'none' if the data is not suitable (e.g. returns a single row/value, unstructured text, or has less than 2 rows).\n"
        "2. If recommended, 'x' must be a column name present in the column list.\n"
        "3. If recommended, 'y' must be a column name present in the column list (should be a numeric metric, count, or value column for 'bar', 'line', 'scatter', 'pie').\n"
        "4. Output ONLY a valid JSON object matching this schema:\n"
        "{\n"
        "  \"chart_type\": \"bar|line|scatter|pie|histogram|none\",\n"
        "  \"x\": \"column_name_or_null\",\n"
        "  \"y\": \"column_name_or_null\",\n"
        "  \"title\": \"Chart Title or null\"\n"
        "}"
    )
    user_prompt = (
        f"User Query: {user_query}\n"
        f"SQL: {sql}\n"
        f"Columns: {df_columns}\n"
        f"Sample Data (top 3 rows): {sample_data_json}\n\n"
        "Recommend chart configuration:"
    )
    try:
        output = llm.generate_chat(sys_prompt, user_prompt, temperature=0.0)
        clean_json = re.sub(r"```[a-zA-Z]*", "", output).strip()
        data = json.loads(clean_json)
        if isinstance(data, dict) and "chart_type" in data:
            return data
    except Exception:
        pass
    return {"chart_type": "none", "x": None, "y": None, "title": None}

def insight_synthesis_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Synthesizing analysis results..."]
    llm = state["llm_client"]
    privacy = state["privacy_level"]
    user_query = state["user_query"]
    sql = state["generated_sql"]
    
    intent = state.get("intent", "chat")
    requires_clarification = state.get("requires_clarification", False)
    
    # If conversational mode was triggered or clarification is needed, skip SQL result processing
    if intent not in ["business_query", "followup_business_query"] or requires_clarification:
        steps.append("Workflow completed successfully (Conversational/Clarification).")
        return {
            "steps_log": steps
        }
        
    # Check if generator returned insufficient information
    if sql.strip().upper() == "INSUFFICIENT_INFORMATION":
        steps.append("Workflow completed successfully (Insufficient Information).")
        return {
            "compiled_natural_insight": "I do not have sufficient information in the database schema to answer your request.",
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
        
    chart_recommendation = {"chart_type": "none", "x": None, "y": None, "title": None}
    df = state.get("sql_results_df")
    if df is not None and not df.empty and len(df) >= 2:
        df_columns = list(df.columns)
        try:
            sample_data_json = df.head(3).to_json(orient="records")
            chart_recommendation = recommend_chart(user_query, sql, df_columns, sample_data_json, llm)
        except Exception:
            pass

    steps.append("Workflow completed successfully.")
    
    return {
        "compiled_natural_insight": insight,
        "chart_recommendation": chart_recommendation,
        "steps_log": steps
    }
