from typing import TypedDict, List, Dict, Any, Optional
import pandas as pd
from llm import LLMClient

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
~