import re
import json
import logging
from typing import TypedDict, List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from langgraph.graph import StateGraph, END

# Import local utilities
from db_utils import BUSINESS_GLOSSARY, SEMANTIC_COLUMN_DESCRIPTIONS, compile_ddl
from llm_client import LLMClient

# Configure logging
logger = logging.getLogger(__name__)

# ==========================================
# 1. LANGGRAPH STATE SCHEMA
# ==========================================

class AgentState(TypedDict):
    # Inputs
    user_query: str
    database_connection_uri: str
    llm_client: LLMClient
    metadata_catalog: Dict[str, Any]
    privacy_level: str  # "Standard", "DDL Only", "DDL + Sample Rows"
    chat_history: List[Dict[str, str]]
    
    # Internal state / Output
    is_db_query: bool
    pruning_reason: str
    pruned_schemas: List[str]
    pruned_table_names: List[str]
    generated_sql: str
    sql_results: Optional[List[Dict[str, Any]]]
    sql_results_df: Optional[pd.DataFrame]
    error_logs: List[Dict[str, Any]]
    attempt_count: int
    compiled_natural_insight: str
    
    # Progress logs for UI rendering
    steps_log: List[str]


# ==========================================
# 2. WORKFLOW GRAPH NODES
# ==========================================

# Node 0: Intent Classifier
def intent_classifier_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Classifying user intent & chat context..."]
    user_query = state["user_query"]
    llm = state["llm_client"]
    chat_history = state.get("chat_history", [])
    catalog = state.get("metadata_catalog", {})
    
    # List of tables currently in the catalog
    table_names = list(catalog.keys())
    
    # 1. Hardcoded Metadata Interceptor for Business Roles
    meta_patterns = [
        r"\bhow many tables\b", 
        r"\blist tables\b", 
        r"\bshow tables\b", 
        r"\btable names\b", 
        r"\bwhat tables\b", 
        r"\bdatabase tables\b", 
        r"\bsqlite_master\b", 
        r"\binformation_schema\b"
    ]
    is_meta_query = False
    for pat in meta_patterns:
        if re.search(pat, user_query, re.IGNORECASE):
            is_meta_query = True
            break
            
    # 2. Hardcoded Schema Inspection Interceptor to prevent structural leakage
    schema_patterns = [
        r"\btable structure\b",
        r"\bcolumns in\b",
        r"\bfields in\b",
        r"\btable schema\b",
        r"\bdescribe table\b",
        r"\bstructure of\b",
        r"\bdefinition of\b",
        r"\bcolumn names\b",
        r"\bwhat attributes\b",
        r"\bwhat fields\b",
        r"\bwhat columns\b"
    ]
    is_schema_query = False
    for pat in schema_patterns:
        if re.search(pat, user_query, re.IGNORECASE):
            is_schema_query = True
            break
            
    if is_meta_query or is_schema_query:
        steps.append("Classified intent: Blocked Metadata / Schema Query")
        return {
            "is_db_query": False,
            "compiled_natural_insight": (
                "I am configured to answer business questions about Academic Administrations, "
                "Financial Ledgers, and Hostel Records. I cannot provide internal database structures, "
                "table schemas, or column definitions for security reasons."
            ),
            "steps_log": steps
        }
        
    # Format chat history context
    history_str = ""
    if chat_history:
        history_str = "Conversation History:\n" + "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-5:]])
        
    classifier_system_prompt = (
        "You are an intent classifier for a SQL database agent. Analyze the user's current message and determine if it "
        "requires querying a database table to retrieve actual data records (e.g. list student names, calculate grades, count orders), "
        "or if it is a general conversational remark or a metadata question asking about the database structure itself "
        "(e.g. greetings, thanks, chitchat, explain capabilities, table counts, what tables are available, columns in table X, list table names).\n\n"
        f"You have direct access to the list of tables currently loaded in the database catalog: {table_names}.\n\n"
        "Output ONLY a valid JSON object with exactly two keys:\n"
        '- "is_db_query": true/false\n'
        '- "conversational_response": string response if "is_db_query" is false. IMPORTANT: If the user is asking about table structures, schemas, count of tables, list of tables, columns, or field names, you MUST set "is_db_query": false and return EXACTLY: "I am configured to answer business questions about Academic Administrations, Financial Ledgers, and Hostel Records. I cannot provide internal database structures, table schemas, or column definitions for security reasons."\n\n'
        "Do not include any markdown tags (like ```json), notes, or explanations outside the JSON."
    )
    
    classifier_user_prompt = f"{history_str}\n\nUser Message: {user_query}\n\nOutput JSON classification:"
    
    llm_output = llm.generate_chat(classifier_system_prompt, classifier_user_prompt, temperature=0.0)
    
    is_db_query = True
    conversational_response = None
    try:
        clean_json = re.sub(r"```[a-zA-Z]*", "", llm_output).strip()
        data = json.loads(clean_json)
        is_db_query = data.get("is_db_query", True)
        conversational_response = data.get("conversational_response")
    except Exception as e:
        logger.error(f"Error parsing classifier JSON: {e}. Output was: {llm_output}")
        is_db_query = True
        
    if not is_db_query:
        steps.append("Classified intent: Conversational / Metadata Chat")
        return {
            "is_db_query": False,
            "compiled_natural_insight": conversational_response or "Hello! I am your database assistant. How can I help you query the database today?",
            "steps_log": steps
        }
    else:
        steps.append("Classified intent: Database Retrieval Query")
        return {
            "is_db_query": True,
            "steps_log": steps
        }


# Node 1: Table Selector & DDL Pruner
def metadata_pruner_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Pruning schemas: Scanning table descriptors..."]
    catalog = state["metadata_catalog"]
    user_query = state["user_query"]
    llm = state["llm_client"]
    chat_history = state.get("chat_history", [])
    
    # Format chat history context to resolve conversational references
    history_str = ""
    if chat_history:
        history_str = "Conversation History:\n" + "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-5:]])
        
    # Format the table index for the LLM
    catalog_description = ""
    for tbl_name, meta in catalog.items():
        cols_summary = ", ".join([c["name"] for c in meta["columns"][:8]])
        if len(meta["columns"]) > 8:
            cols_summary += ", ..."
        desc = BUSINESS_GLOSSARY.get(tbl_name, meta['description'])
        catalog_description += f"- Table: `{tbl_name}` | Columns: [{cols_summary}] | Description: {desc}\n"
        
    sys_prompt = (
        "You are an expert DB architect. Analyze the user question (and conversation history, if any) "
        "and select the top 3 to 5 tables from the catalog needed to write the SQL query.\n\n"
        "Crucial Guidelines for Table Selection:\n"
        "1. Identify all entities in the query. If the query refers to relationship mappings (e.g. what courses teachers teach), "
        "you MUST select both the primary entity tables ('instructors', 'courses') AND the connecting link tables ('sections'). "
        "Do not omit entity lookup tables containing titles or names, otherwise the SQL generator won't know the exact column descriptors (like course_title).\n"
        "2. Output ONLY a valid JSON object with exactly two keys:\n"
        '- "tables": a list of string table names\n'
        '- "reasoning": a string explaining why these tables were selected and how they relate to the user\'s query.\n\n'
        "Do not write markdown tags (like ```json), explanations, or notes outside the JSON structure."
    )
    
    user_prompt = (
        f"{history_str}\n\n"
        f"User Question: {user_query}\n\n"
        f"Available Database Catalog:\n{catalog_description}\n\n"
        "Output JSON selection:"
    )
    
    llm_output = llm.generate_chat(sys_prompt, user_prompt, temperature=0.0)
    
    selected_tables = []
    pruning_reason = "No reasoning provided."
    try:
        clean_json = re.sub(r"```[a-zA-Z]*", "", llm_output).strip()
        data = json.loads(clean_json)
        selected_tables = data.get("tables", [])
        pruning_reason = data.get("reasoning", "Selected tables based on schema matching.")
        selected_tables = [t for t in selected_tables if t in catalog]
    except Exception as e:
        logger.error(f"Error parsing selected tables JSON: {e}. Output was: {llm_output}")
        selected_tables = list(catalog.keys())[:4]
        pruning_reason = "Fallback: selected default tables due to parsing error."
        
    if not selected_tables:
        selected_tables = list(catalog.keys())[:4]
        pruning_reason = "Fallback: selected default tables."
        
    steps.append(f"Pruned Context: Selected table structures for: {', '.join(selected_tables)}")
    
    # Compile the DDL structures for the selected tables
    pruned_ddls = []
    for tbl in selected_tables:
        pruned_ddls.append(compile_ddl(tbl, catalog[tbl]))
        
    return {
        "pruned_schemas": pruned_ddls,
        "pruned_table_names": selected_tables,
        "pruning_reason": pruning_reason,
        "steps_log": steps
    }


# Node 2: SQL Generator
def sql_generation_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Generating database queries..."]
    dialect = "sqlite" if "sqlite" in state["database_connection_uri"].lower() else "standard sql"
    
    llm = state["llm_client"]
    user_query = state["user_query"]
    chat_history = state.get("chat_history", [])
    pruned_ddls = "\n\n".join(state["pruned_schemas"])
    attempt = state.get("attempt_count", 0) + 1
    
    # Format chat history context
    history_str = ""
    if chat_history:
        history_str = "Conversation History:\n" + "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-5:]])
        
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
            
    sys_prompt = (
        f"You are a database engineer generating clean SQL for {dialect}. "
        "Analyze the user question, previous context, and the provided DDL schema, then generate "
        "the SQL query.\n\n"
        "Follow these strict directives:\n"
        "1. Produce ONLY a SELECT query or Common Table Expression (WITH).\n"
        "2. Do not write markdown markers, notes, or explanation. Output ONLY raw SQL code.\n"
        "3. Use standard SQL joins, groupings, aggregate clauses, and subqueries as required.\n"
        "4. DO NOT attempt to write or edit values (INSERT/UPDATE/DELETE/DROP/ALTER are strictly forbidden)."
    )
    
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


# Node 3: Security Sanitization & Execution
def security_and_execution_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Validating query syntax & security permissions..."]
    sql = state["generated_sql"]
    errors = state.get("error_logs", [])
    
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


# Node 4: Insight Synthesis
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


# ==========================================
# 3. CONDITIONAL ROUTING & GRAPH COMPILATION
# ==========================================

def route_intent(state: AgentState):
    """Determines whether to query metadata and generate SQL or skip directly to synthesis."""
    if not state.get("is_db_query", True):
        return "insight_synthesis_node"
    return "metadata_pruner_node"


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
x`x`

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