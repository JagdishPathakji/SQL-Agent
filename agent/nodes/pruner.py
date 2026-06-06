import re
import json
import logging
from typing import Dict, Any
from ..state import AgentState
from ..config import MAX_HISTORY_MESSAGES
from database import BUSINESS_GLOSSARY, compile_ddl

logger = logging.getLogger(__name__)

def metadata_pruner_node(state: AgentState) -> Dict[str, Any]:
    steps = state.get("steps_log", []) + ["Pruning schemas: Scanning table descriptors..."]
    catalog = state["metadata_catalog"]
    user_query = state["user_query"]
    llm = state["llm_client"]
    chat_history = state.get("chat_history", [])
    
    business_glossary = state.get("business_glossary")
    if not business_glossary:
        business_glossary = {tbl: meta.get("description", f"Table containing information about {tbl}.") for tbl, meta in catalog.items()}
    column_descriptions = state.get("column_descriptions")
    
    # Format chat history context to resolve conversational references
    history_str = ""
    if chat_history:
        history_str = "Conversation History:\n" + "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-MAX_HISTORY_MESSAGES:]])
        
    # Format the table index for the LLM
    catalog_description = ""
    for tbl_name, meta in catalog.items():
        cols_summary = ", ".join([c["name"] for c in meta["columns"][:8]])
        if len(meta["columns"]) > 8:
            cols_summary += ", ..."
        desc = business_glossary.get(tbl_name, meta['description'])
        catalog_description += f"- Table: `{tbl_name}` | Columns: [{cols_summary}] | Description: {desc}\n"
        
    sys_prompt = """
You are an expert database architect responsible for schema context selection.

Your task is to determine the minimum set of database tables required to answer the user's question.

Guidelines:

1. Identify the business entities mentioned or implied.
2. Resolve references from conversation history.
3. Select only the tables necessary to answer the question.
4. Include bridge/link tables required for joins.
5. Include lookup tables containing business names or descriptors.
6. Avoid redundant or unrelated tables.
7. Prefer the smallest sufficient table set.
8. Consider both direct and indirect relationships.
9. If the question is ambiguous, indicate clarification is required.
10. Do not invent tables or relationships.

Output ONLY valid JSON:

{
    "tables": [],
    "important_columns": {},
    "join_paths": [],
    "needs_clarification": false,
    "selection_reason": ""
}

Where:

tables:
- selected table names

important_columns:
- columns likely required by SQL generation

join_paths:
- inferred relationships between selected tables

needs_clarification:
- true if user intent is ambiguous

selection_reason:
- short explanation
}
"""
    
    user_prompt = (
        f"{history_str}\n\n"
        f"User Question: {user_query}\n\n"
        f"Available Database Catalog:\n{catalog_description}\n\n"
        "Output JSON selection:"
    )
    
    llm_output = llm.generate_chat(sys_prompt, user_prompt, temperature=0.0)
    
    selected_tables = []
    pruning_reason = "No reasoning provided."
    needs_clarification = False
    try:
        # Robust JSON extraction: locate first '{' and last '}'
        start_idx = llm_output.find('{')
        end_idx = llm_output.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            clean_json = llm_output[start_idx:end_idx+1].strip()
        else:
            clean_json = re.sub(r"```[a-zA-Z]*", "", llm_output).strip()
            
        data = json.loads(clean_json)
        selected_tables = data.get("tables", [])
        pruning_reason = data.get("selection_reason", "Selected tables based on schema matching.")
        needs_clarification = data.get("needs_clarification", False)
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
        pruned_ddls.append(compile_ddl(tbl, catalog[tbl], column_descriptions=column_descriptions))
        
    state_updates = {
        "pruned_schemas": pruned_ddls,
        "pruned_table_names": selected_tables,
        "pruning_reason": pruning_reason,
        "steps_log": steps
    }
    
    # Trigger clarification if pruner detects schema selection ambiguity
    if needs_clarification:
        state_updates["requires_clarification"] = True
        state_updates["clarification_message"] = (
            f"I found the request slightly ambiguous during database planning (Reason: {pruning_reason}). "
            "Could you please specify what info you are seeking?"
        )
        
    return state_updates
