import re
import json
import logging
from typing import Dict, Any
from sqlalchemy import create_engine, text
from ..state import AgentState
from ..config import MAX_HISTORY_MESSAGES

logger = logging.getLogger(__name__)

def sql_generation_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Generating database queries..."]
    
    # Bypass SQL generation if clarification has been requested by the pruner
    if state.get("requires_clarification", False):
        steps.append("Bypassing query generation due to clarification request.")
        return {
            "generated_sql": "INSUFFICIENT_INFORMATION",
            "steps_log": steps
        }
        
    dialect = "sqlite" if "sqlite" in state["database_connection_uri"].lower() else "standard sql"
    
    llm = state["llm_client"]
    user_query = state["user_query"]
    chat_history = state.get("chat_history", [])
    pruned_ddls = "\n\n".join(state["pruned_schemas"])
    attempt = state.get("attempt_count", 0) + 1
    
    # Format chat history context
    history_str = ""
    if chat_history:
        history_str = "Conversation History:\n" + "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-MAX_HISTORY_MESSAGES:]])
        
    # Handle sample rows if privacy level allows it
    sample_rows_section = ""
    if state["privacy_level"] == "DDL + Sample Rows":
        sample_rows_section = "### Sample Rows for Column Reference:\n"
        engine = create_engine(state["database_connection_uri"])
        with engine.connect() as conn:
            for tbl in state["pruned_table_names"]:
                try:
                    res = conn.execute(text(f"SELECT * FROM {tbl} LIMIT 1;"))
                    if res.returns_rows:
                        row = res.fetchone()
                        if row:
                            row_dict = dict(row._mapping)
                            sample_rows_section += f"- Table `{tbl}` sample record: {json.dumps(row_dict, default=str)}\n"
                except Exception as e:
                    logger.warning(f"Could not load sample row for {tbl}: {e}")
        engine.dispose()
        
    # Generate error history if self-healing is triggered
    error_section = ""
    if state.get("error_logs"):
        error_section = "### Previous Execution Errors (Analyze and Correct):\n"
        for i, log in enumerate(state["error_logs"]):
            error_section += f"Attempt {i+1} SQL: {log['sql']}\nError: {log['error']}\n\n"
            
    sys_prompt = f"""
You are a senior database engineer generating SQL for {dialect}.

You are provided:
- User question
- Conversation context
- Approved database schema (DDL)

Requirements:

1. Generate ONLY a single read-only SQL statement.
2. Allowed statements:
   - SELECT
   - WITH (CTE)

3. Forbidden:
   - INSERT
   - UPDATE
   - DELETE
   - MERGE
   - UPSERT
   - DROP
   - ALTER
   - TRUNCATE
   - CREATE
   - GRANT
   - REVOKE

4. Use ONLY tables and columns present in the provided schema.
5. Never invent tables, columns, relationships, or business entities.
6. Verify all referenced identifiers exist in the schema.
7. Never query metadata catalogs:
   - information_schema
   - pg_catalog
   - sqlite_master
   - sys

8. Never use SELECT *.
9. Select only required columns.
10. Use only necessary joins.
11. Generate SQL strictly compatible with {dialect}.
12. If aggregation is required, use proper GROUP BY clauses.
13. If the request is ambiguous or cannot be answered from the schema, return exactly:

INSUFFICIENT_INFORMATION

14. Output raw SQL only.
15. Do not output markdown.
16. Do not output explanations.
17. Do not output comments.

Output:
Either:
- A valid SQL query

OR

- INSUFFICIENT_INFORMATION
"""
    
    user_prompt = (
        f"{history_str}\n\n"
        f"User Question: {user_query}\n\n"
        f"DDL Schemas:\n{pruned_ddls}\n\n"
        f"{sample_rows_section}\n"
        f"{error_section}\n"
        "Generate the SQL query:"
    )
    
    sql_query = llm.generate_chat(sys_prompt, user_prompt, temperature=0.0).strip()
    
    sql_query = re.sub(r"^```sql\s*", "", sql_query, flags=re.IGNORECASE)
    sql_query = re.sub(r"```$", "", sql_query)
    sql_query = sql_query.strip().rstrip(';')
    
    steps.append(f"Drafted query (Attempt {attempt})")
    
    return {
        "generated_sql": sql_query,
        "attempt_count": attempt,
        "steps_log": steps
    }
