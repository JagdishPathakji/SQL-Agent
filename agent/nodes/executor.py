import re
import logging
from typing import Dict, Any
import pandas as pd
from sqlalchemy import create_engine, text
from ..state import AgentState

logger = logging.getLogger(__name__)

def security_and_execution_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Validating query syntax & security permissions..."]
    sql = state["generated_sql"]
    errors = state.get("error_logs", [])
    
    # Intercept insufficient information indicators immediately
    if sql.strip().upper() == "INSUFFICIENT_INFORMATION":
        steps.append("Database generator reported INSUFFICIENT_INFORMATION. Skipping execution.")
        return {
            "sql_results": [],
            "sql_results_df": pd.DataFrame(),
            "steps_log": steps
        }
    
    # 1. Structural Pre-Execution Sanitization (Security Guardrails)
    forbidden_keywords = ["drop", "insert", "update", "delete", "alter", "truncate", "grant", "create", "replace"]
    for keyword in forbidden_keywords:
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, sql, re.IGNORECASE):
            security_err = f"Security Violation: Forbidden keyword '{keyword.upper()}' detected. Query rejected."
            steps.append("Security metrics evaluation: BLOCKED")
            logger.warning(security_err)
            return {
                "error_logs": errors + [{"sql": sql, "error": security_err}],
                "steps_log": steps
            }
            
    # 2. Injection/Jailbreak Protection
    cleaned_sql = sql.strip().lstrip('(').strip()
    if not (cleaned_sql.upper().startswith("SELECT") or cleaned_sql.upper().startswith("WITH")):
        inject_err = "Security Violation: Non-SELECT operation attempted. Only SELECT queries are permitted."
        steps.append("Security structural evaluation: BLOCKED")
        logger.warning(inject_err)
        return {
            "error_logs": errors + [{"sql": sql, "error": inject_err}],
            "steps_log": steps
        }
        
    system_metadata_patterns = ["sqlite_master", "sqlite_sequence", "sqlite_stat", "pg_shadow", "pg_user", "pg_authid", "information_schema", "mysql."]
    for pattern in system_metadata_patterns:
        if pattern.lower() in sql.lower():
            sys_err = f"Security Violation: Access to system catalogs ({pattern}) is restricted."
            steps.append("Security catalog validation: BLOCKED")
            logger.warning(sys_err)
            return {
                "error_logs": errors + [{"sql": sql, "error": sys_err}],
                "steps_log": steps
            }
            
    # 3. Read-Only Database Execution
    steps.append("Security checks passed. Executing database retrieval transaction...")
    engine = create_engine(state["database_connection_uri"])
    dialect = engine.dialect.name
    
    results = None
    df = None
    
    try:
        with engine.connect() as conn:
            # Set session-level read-only variables where supported
            if dialect == "postgresql":
                conn.execute(text("SET TRANSACTION READ ONLY;"))
                
            # Perform query
            db_res = conn.execute(text(sql))
            if db_res.returns_rows:
                rows = db_res.all()
                results = [dict(r._mapping) for r in rows]
                df = pd.DataFrame(results)
                steps.append(f"Successfully retrieved {len(results)} rows.")
            else:
                results = []
                df = pd.DataFrame()
                steps.append("Executed successfully (no rows returned).")
                
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Database execution error: {error_msg}")
        errors.append({"sql": sql, "error": error_msg})
        steps.append(f"Execution failed (Attempt {state['attempt_count']}): {error_msg[:100]}...")
    finally:
        engine.dispose()
        
    return {
        "sql_results": results,
        "sql_results_df": df,
        "error_logs": errors,
        "steps_log": steps
    }
