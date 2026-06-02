import os
import streamlit as st
import pandas as pd
from db_utils import (
    generate_college_erp_db,
    crawl_database_metadata
)
from llm_client import LLMClient
from graph_agent import build_workflow_graph


# Set up Streamlit page configuration with a premium dark theme feel
st.set_page_config(
    page_title="Enterprise SQL Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-title {
        font-family: 'Outfit', sans-serif;
        font-size: 3rem;
        background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 1.2rem;
        border-left: 5px solid #6366f1;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 1rem;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-value {
        font-size: 1.8rem;
        color: #f1f5f9;
        font-weight: 700;
    }
    
    /* Code styling */
    .sql-code-box {
        background-color: #0f172a;
        color: #38bdf8;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #334155;
        font-family: 'Courier New', Courier, monospace;
        margin-bottom: 1rem;
    }
    
    /* System status */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 9999px;
        margin-bottom: 0.5rem;
    }
    .status-success {
        background-color: #064e3b;
        color: #34d399;
    }
    .status-warning {
        background-color: #78350f;
        color: #fbbf24;
    }
    .status-danger {
        background-color: #7f1d1d;
        color: #f87171;
    }
</style>
""", unsafe_allow_html=True)

# Define Sandbox DB File Path
DB_FILE = os.path.join(os.getcwd(), "college_erp.db").replace("\\", "/")

# Initialize database if not exists
if not os.path.exists(DB_FILE):
    with st.spinner("Initializing College ERP Sandbox DB (22 Tables)..."):
        generate_college_erp_db(DB_FILE)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "metadata_catalog" not in st.session_state:
    st.session_state.metadata_catalog = {}
if "total_tables" not in st.session_state:
    st.session_state.total_tables = 0
if "current_uri" not in st.session_state:
    st.session_state.current_uri = ""
if "pruned_count" not in st.session_state:
    st.session_state.pruned_count = 0

# ==========================================
# SIDEBAR CONFIGURATION
# ==========================================

st.sidebar.markdown("<h2 style='color:#f1f5f9;font-family:Outfit;margin-bottom:0px;'>⚙️ Configuration</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#64748b;font-size:0.85rem;margin-top:0px;margin-bottom:20px;'>Enterprise SQL Agent Setup</p>", unsafe_allow_html=True)

# 1. Database Connection Selectors
with st.sidebar.expander("🔌 Database Connection", expanded=True):
    db_mode = st.radio(
        "Connection Mode",
        ["Use Sample Enterprise Environment", "Connect Custom Production Database"]
    )

    if db_mode == "Use Sample Enterprise Environment":
        connection_uri = f"sqlite:///{DB_FILE}"
    else:
        connection_uri = st.text_input(
            "Database Connection URI",
            placeholder="postgresql://user:pass@host:5432/dbname",
            help="Input a standard SQLAlchemy connection string. Ensure driver library is installed."
        )
        st.caption("🔒 **Security Policy**: For safety in enterprise networks, ensure credentials belong to a restricted read-only database user.")

    # Normalize SQLite backslashes to forward slashes for Windows URL parsing
    if connection_uri and connection_uri.startswith("sqlite:///"):
        connection_uri = "sqlite:///" + connection_uri[10:].replace("\\", "/")

    # Manage database metadata sync
    trigger_sync = False
    if db_mode == "Use Sample Enterprise Environment":
        if st.session_state.current_uri != connection_uri:
            st.session_state.current_uri = connection_uri
            with st.spinner("Syncing Sandbox Metadata Catalog..."):
                catalog = crawl_database_metadata(connection_uri)
                st.session_state.metadata_catalog = catalog
                st.session_state.total_tables = len(catalog)
    else:
        if connection_uri:
            if st.button("🔄 Sync Database Catalog", use_container_width=True):
                trigger_sync = True
        else:
            st.info("Please input a valid connection string to sync the database schema.")

if trigger_sync and connection_uri:
    with st.spinner("Crawling database schemas & tables..."):
        try:
            catalog = crawl_database_metadata(connection_uri)
            st.session_state.metadata_catalog = catalog
            st.session_state.total_tables = len(catalog)
            st.session_state.current_uri = connection_uri
            st.success(f"Crawled {len(catalog)} tables successfully!")
        except Exception as e:
            st.error(f"Catalog sync failed: {str(e)}")

# 2. Dynamic LLM Setup
with st.sidebar.expander("🧠 LLM Brain Credentials", expanded=True):
    llm_provider = st.selectbox(
        "Provider",
        ["Gemini", "OpenAI", "Groq", "Ollama", "Custom (OpenAI Compatible)"]
    )

    # Popular models index to avoid typos
    model_options = {
        "Gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro", "Other / Custom Model"],
        "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "Other / Custom Model"],
        "Groq": ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "Other / Custom Model"],
        "Ollama": ["llama3", "mistral", "codellama", "phi3", "Other / Custom Model"],
        "Custom (OpenAI Compatible)": ["Other / Custom Model"]
    }

    selected_model_option = st.selectbox("Model Name", model_options.get(llm_provider, ["Other / Custom Model"]))

    if selected_model_option == "Other / Custom Model":
        llm_model = st.text_input("Custom Model Identifier", value="", placeholder="e.g. llama-3.1-8b-instant")
    else:
        llm_model = selected_model_option

    # API key requirements
    if llm_provider == "Ollama":
        api_key = "ollama"  # dummy key
    else:
        api_key = st.text_input(
            f"{llm_provider} API Key",
            type="password",
            value=os.getenv(f"{llm_provider.upper()}_API_KEY", "")
        )

    # Base URL override
    custom_base_url = None
    if llm_provider in ["Ollama", "Custom (OpenAI Compatible)"]:
        default_url = "http://localhost:11434/v1" if llm_provider == "Ollama" else ""
        custom_base_url = st.text_input("Base URL Override", value=default_url)

# 3. Data Privacy Selection
with st.sidebar.expander("🛡️ Privacy Settings", expanded=False):
    privacy_level = st.radio(
        "Privacy Restriction Level",
        [
            "Standard (Full Insights)", 
            "DDL Only (Strict Privacy)", 
            "DDL + Sample Rows (Local execution)"
        ],
        help=(
            "Standard sends schemas and query results to the LLM. "
            "DDL Only sends only table schemas (no database rows or sample rows) to LLM. "
            "DDL + Sample Rows sends schema metadata and 1 sample row to LLM, but query results remain purely local."
        )
    )

# 4. Metric Displays
st.sidebar.markdown("<hr/>", unsafe_allow_html=True)
st.sidebar.markdown("<h3 style='color:#f1f5f9;font-size:1.1rem;font-family:Outfit;'>📊 Session Telemetry</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"""
<div class="metric-card">
    <div class="metric-label">Total Catalog Tables</div>
    <div class="metric-value">{st.session_state.total_tables}</div>
</div>
<div class="metric-card" style="border-left: 5px solid #a855f7;">
    <div class="metric-label">LLM Context Tables (Last Query)</div>
    <div class="metric-value">{st.session_state.pruned_count}</div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# MAIN INTERFACE CANVAS
# ==========================================

st.markdown("<h1 class='main-title'>⚡ Enterprise SQL Agent</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>A safe, self-healing natural language query agent powered by LangGraph.</div>", unsafe_allow_html=True)

# Informative Banner
if not st.session_state.metadata_catalog:
    st.warning("⚠️ No active catalog synced. Please select Sandbox Mode or enter a custom database URI and click 'Sync Database Catalog'.")
    st.stop()

# Print Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        # Display table context detail
        if "pruned_tables" in msg and msg["pruned_tables"]:
            st.markdown(f"🔍 **Table Context**: {', '.join([f'`{t}`' for t in msg['pruned_tables']])}")
            if "pruning_reason" in msg and msg["pruning_reason"]:
                st.caption(f"💡 *Why:* {msg['pruning_reason']}")
                
        # Display execution details if available
        if "sql" in msg and msg["sql"]:
            with st.expander("🛠️ Executed SQL Query"):
                st.code(msg["sql"], language="sql")
                
        if "dataframe" in msg and msg["dataframe"] is not None:
            df = msg["dataframe"]
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No records returned.")

# User prompt
placeholder_text = (
    "Ask a question about the college ERP (e.g. Find the average grade of active students in Turing Hall)"
    if db_mode == "Use Sample Enterprise Environment"
    else "Ask a question about your database (e.g. List top 5 rows from table X)"
)
user_query = st.chat_input(placeholder_text)

if user_query:
    # 1. Render User Message
    st.chat_message("user").write(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # 2. Build LLM Client
    if not api_key:
        st.error("Missing API Key. Please provide your provider's API key in the settings panel.")
        st.stop()
        
    llm_client = LLMClient(
        provider=llm_provider,
        api_key=api_key,
        model_name=llm_model,
        base_url=custom_base_url
    )
    
    # 3. Trigger LangGraph Workflow Execution
    with st.chat_message("assistant"):
        workflow = build_workflow_graph()
        
        # Extract previous messages for chat history
        chat_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
        
        # Initial input state
        state_input = {
            "user_query": user_query,
            "database_connection_uri": connection_uri,
            "llm_client": llm_client,
            "metadata_catalog": st.session_state.metadata_catalog,
            "privacy_level": privacy_level.split(" (")[0],  # Get "Standard", "DDL Only", etc.
            "chat_history": chat_history,
            "is_db_query": True,
            "pruning_reason": "",
            "pruned_schemas": [],
            "pruned_table_names": [],
            "generated_sql": "",
            "sql_results": None,
            "sql_results_df": None,
            "error_logs": [],
            "attempt_count": 0,
            "compiled_natural_insight": "",
            "steps_log": []
        }
        
        # Real-time state progress visualization
        last_step_count = 0
        status_box = st.status("Analyzing user intent...", expanded=True)
        
        # Stream the nodes of the graph execution
        final_state = state_input
        for event in workflow.stream(state_input):
            node_name = list(event.keys())[0]
            node_output = event[node_name]
            final_state.update(node_output)
            
            # Show progress in real-time
            steps_log = final_state.get("steps_log", [])
            for i in range(last_step_count, len(steps_log)):
                status_box.write(f"⚙️ {steps_log[i]}")
            last_step_count = len(steps_log)
            
            # Update status box title
            if node_name == "intent_classifier_node":
                if final_state.get("is_db_query", True):
                    status_box.update(label="Analyzing database metadata and pruning table structures...")
                else:
                    status_box.update(label="Conversational intent detected. Formulating chat response...")
            elif node_name == "metadata_pruner_node":
                status_box.update(label="Metadata context selected. Generating optimized SQL...")
            elif node_name == "sql_generation_node":
                status_box.update(label="Query generated. Running validation checks...")
            elif node_name == "security_and_execution_node":
                if final_state.get("sql_results") is not None:
                    status_box.update(label="Database executed successfully. Formulating insights...")
                else:
                    status_box.update(label="Error in query execution. Attempting self-healing correction...")
            elif node_name == "insight_synthesis_node":
                status_box.update(label="Insights completed.")
                
        status_box.update(label="Execution Finished", state="complete", expanded=False)
        
        # 4. Display Outputs to UI
        # Get outcomes
        sql = final_state.get("generated_sql", "")
        df = final_state.get("sql_results_df")
        insight = final_state.get("compiled_natural_insight", "")
        pruned_tables = final_state.get("pruned_table_names", [])
        pruning_reason = final_state.get("pruning_reason", "")
        is_db_query = final_state.get("is_db_query", True)
        
        # Update metrics sidebar
        st.session_state.pruned_count = len(pruned_tables)
        
        # Output Selected Tables and Selection Criteria
        if is_db_query and pruned_tables:
            st.markdown(f"🔍 **Table Context Selected**: {', '.join([f'`{t}`' for t in pruned_tables])}")
            if pruning_reason:
                st.info(f"💡 **Why these tables were selected**: {pruning_reason}")
                
        # Output SQL
        if is_db_query and sql:
            with st.expander("🛠️ Executed SQL Query", expanded=False):
                st.code(sql, language="sql")
                
        # Output Data Table
        if is_db_query and df is not None:
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("The query returned an empty dataset.")
        
        # Output Narrative Insight
        if "ERROR:" in insight:
            st.error(f"🤖 **LLM Connection Error**: The LLM provider returned an error during execution. This usually means your API Key is incorrect, or the selected Model Name is invalid for this provider.\n\n**Details:**\n`{insight}`")
        else:
            st.write(insight)
        
        # Add Assistant message to persistent history
        st.session_state.messages.append({
            "role": "assistant",
            "content": insight,
            "sql": sql if is_db_query else "",
            "dataframe": df if is_db_query else None,
            "pruned_tables": pruned_tables if is_db_query else [],
            "pruning_reason": pruning_reason if is_db_query else ""
        })
        
        # Rerun to refresh metrics sidebar with latest pruned table count
        st.rerun()
