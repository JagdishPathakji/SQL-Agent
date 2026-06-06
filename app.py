import os
import streamlit as st
import pandas as pd
from database import (
    generate_college_erp_db,
    crawl_database_metadata
)
from llm import LLMClient
from agent import build_workflow_graph



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
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Core layout background and fonts */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Main app layout override to dark SaaS */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.08) 0%, transparent 45%), 
                    radial-gradient(circle at 85% 85%, rgba(168, 85, 247, 0.08) 0%, transparent 45%), 
                    #090d16 !important;
    }
    
    /* Header background transparent */
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0c0f1a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 2rem !important;
    }
    
    /* Elegant Title and Subtitle */
    .main-title {
        font-family: 'Outfit', sans-serif !important;
        font-size: 3rem !important;
        background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #f472b6 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 800 !important;
        margin-bottom: 0.2rem !important;
        letter-spacing: -0.02em !important;
        text-shadow: 0 0 50px rgba(99, 102, 241, 0.15) !important;
    }
    
    .subtitle {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.1rem !important;
        color: #94a3b8 !important;
        margin-bottom: 2rem !important;
        font-weight: 400 !important;
    }
    
    /* Glassmorphism Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.3) !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-left: 4px solid #6366f1 !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        margin-bottom: 1.2rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .metric-card:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(99, 102, 241, 0.25) !important;
        box-shadow: 0 12px 40px 0 rgba(99, 102, 241, 0.1) !important;
    }
    .metric-card.purple-accent {
        border-left: 4px solid #a855f7 !important;
    }
    .metric-card.purple-accent:hover {
        border-color: rgba(168, 85, 247, 0.25) !important;
        box-shadow: 0 12px 40px 0 rgba(168, 85, 247, 0.1) !important;
    }
    
    .metric-label {
        font-size: 0.75rem !important;
        color: #94a3b8 !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin-bottom: 0.4rem !important;
    }
    
    .metric-value {
        font-size: 1.8rem !important;
        color: #f8fafc !important;
        font-weight: 800 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Modernized Form Controls */
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        background-color: rgba(17, 24, 39, 0.6) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        font-size: 0.9rem !important;
        padding: 10px 14px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15) !important;
        background-color: rgba(17, 24, 39, 0.8) !important;
    }
    
    /* Styled Selectbox and Radios */
    div[data-testid="stSelectbox"] > div {
        background-color: rgba(17, 24, 39, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        color: #f8fafc !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stSelectbox"] > div:hover {
        border-color: rgba(124, 58, 237, 0.5) !important;
    }
    div[data-testid="stRadio"] label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        background-color: rgba(15, 23, 42, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    /* Slick Action Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.2) !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.3) !important;
        background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%) !important;
    }
    div.stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Streamlit expander revamp */
    div[data-testid="stExpander"] {
        background: rgba(17, 24, 39, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
        margin-bottom: 1rem !important;
        overflow: hidden !important;
    }
    .streamlit-expanderHeader {
        background-color: transparent !important;
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.02) !important;
        padding: 12px 16px !important;
    }
    .streamlit-expanderHeader:hover {
        background-color: rgba(255, 255, 255, 0.02) !important;
        color: #a78bfa !important;
    }
    
    /* Glassmorphic Chat Messages styling */
    [data-testid="stChatMessage"] {
        background-color: rgba(30, 41, 59, 0.25) !important;
        border: 1px solid rgba(255, 255, 255, 0.03) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        margin-bottom: 1.2rem !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stChatMessage"]:hover {
        border-color: rgba(255, 255, 255, 0.06) !important;
        background-color: rgba(30, 41, 59, 0.35) !important;
    }
    
    /* User chat bubble */
    [data-testid="stChatMessage"][aria-label*="user"] {
        background-color: rgba(99, 102, 241, 0.05) !important;
        border-left: 4px solid #6366f1 !important;
    }
    
    /* Assistant chat bubble */
    [data-testid="stChatMessage"][aria-label*="assistant"] {
        background-color: rgba(168, 85, 247, 0.03) !important;
        border-left: 4px solid #a855f7 !important;
    }
    
    /* Fixed Chat Input container */
    [data-testid="stChatInput"] {
        background-color: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        padding: 8px !important;
        box-shadow: 0 -10px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 25px -5px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #f8fafc !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
    }
    
    /* SQL Code styling */
    .sql-code-box {
        background-color: #090d16 !important;
        color: #38bdf8 !important;
        padding: 1.2rem !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        font-family: 'Fira Code', 'Courier New', Courier, monospace !important;
        font-size: 0.9rem !important;
        margin-bottom: 1rem !important;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.5) !important;
    }
    
    /* System status badges */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 9999px;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .status-success {
        background-color: rgba(16, 185, 129, 0.15) !important;
        color: #34d399 !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }
    .status-warning {
        background-color: rgba(245, 158, 11, 0.15) !important;
        color: #fbbf24 !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
    }
    .status-danger {
        background-color: rgba(239, 68, 68, 0.15) !important;
        color: #f87171 !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }
    ::-webkit-scrollbar-track {
        background: #090d16 !important;
    }
    ::-webkit-scrollbar-thumb {
        background: #1e293b !important;
        border-radius: 4px !important;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155 !important;
    }
</style>
""", unsafe_allow_html=True)

# Define Sandbox DB File Path
DB_FILE = os.path.join(os.getcwd(), "college_erp.db").replace("\\", "/")

def sanitize_df_for_plotting(df):
    if df is None or df.empty:
        return df
    df_clean = df.copy()
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            try:
                converted = pd.to_numeric(df_clean[col], errors='raise')
                df_clean[col] = converted
            except Exception:
                pass
    return df_clean

# Initialize database if not exists
if not os.path.exists(DB_FILE):
    with st.spinner("Initializing College ERP Sandbox DB (22 Tables)..."):
        generate_college_erp_db(DB_FILE)

# Initialize Session State
if "environments" not in st.session_state:
    st.session_state.environments = {
        "sample": {
            "messages": [],
            "metadata_catalog": {},
            "total_tables": 0,
            "current_uri": "",
            "pruned_count": 0,
            "conversation_summary": ""
        },
        "custom": {
            "messages": [],
            "metadata_catalog": {},
            "total_tables": 0,
            "current_uri": "",
            "pruned_count": 0,
            "conversation_summary": ""
        }
    }
if "custom_glossary" not in st.session_state:
    st.session_state.custom_glossary = {}


# ==========================================
# SIDEBAR CONFIGURATION
# ==========================================

st.sidebar.markdown("<h2 style='color:#f8fafc;font-family:Outfit;font-weight:700;font-size:1.5rem;margin-bottom:0px;'>⚙️ Configuration</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#94a3b8;font-size:0.8rem;margin-top:2px;margin-bottom:20px;'>Enterprise SQL Agent Setup</p>", unsafe_allow_html=True)

# 1. Database Connection Selectors
with st.sidebar.expander("🔌 Database Connection", expanded=True):
    db_mode = st.radio(
        "Connection Mode",
        ["Use Sample Enterprise Environment", "Connect Custom Production Database"]
    )
    env_key = "sample" if db_mode == "Use Sample Enterprise Environment" else "custom"

    if db_mode == "Use Sample Enterprise Environment":
        connection_uri = f"sqlite:///{DB_FILE}"
        custom_glossary_json = ""
    else:
        connection_uri = st.text_input(
            "Database Connection URI",
            placeholder="postgresql://user:pass@host:5432/dbname",
            help="Input a standard SQLAlchemy connection string. Ensure driver library is installed."
        )
        st.caption("🔒 **Security Policy**: For safety in enterprise networks, ensure credentials belong to a restricted read-only database user.")
        custom_glossary_json = st.text_area(
            "📖 Optional Business Glossary JSON",
            placeholder='{\n  "business_glossary": {\n    "table_name": "Description of table. Sample Query: \'Query?\' SQL: SELECT col1, col2 FROM table_name;"\n  },\n  "column_descriptions": {\n    "table_name.column_name": "Description of column"\n  }\n}',
            help="Optionally provide custom table descriptions and column descriptions to enhance intent classification and schema pruning. Note: Avoid SELECT * in your sample query fields.",
            height=200
        )

    # Normalize SQLite backslashes to forward slashes for Windows URL parsing
    if connection_uri and connection_uri.startswith("sqlite:///"):
        connection_uri = "sqlite:///" + connection_uri[10:].replace("\\", "/")

    # Manage database metadata sync
    trigger_sync = False
    if db_mode == "Use Sample Enterprise Environment":
        if st.session_state.environments["sample"]["current_uri"] != connection_uri:
            st.session_state.environments["sample"]["current_uri"] = connection_uri
            with st.spinner("Syncing Sandbox Metadata Catalog..."):
                catalog = crawl_database_metadata(connection_uri)
                st.session_state.environments["sample"]["metadata_catalog"] = catalog
                st.session_state.environments["sample"]["total_tables"] = len(catalog)
    else:
        if connection_uri:
            if st.button("🔄 Sync Database Catalog", use_container_width=True):
                trigger_sync = True
        else:
            st.info("Please input a valid connection string to sync the database schema.")

    custom_glossary_dict = {}
    if db_mode != "Use Sample Enterprise Environment" and custom_glossary_json.strip():
        try:
            import json
            parsed = json.loads(custom_glossary_json)
            if isinstance(parsed, dict):
                custom_glossary_dict = parsed
            else:
                st.error("❌ Glossary must be a JSON object/dictionary.")
        except Exception as je:
            st.error(f"❌ Invalid Glossary JSON: {str(je)}")

if trigger_sync and connection_uri:
    with st.spinner("Crawling database schemas & tables..."):
        try:
            catalog = crawl_database_metadata(connection_uri)
            st.session_state.environments["custom"]["metadata_catalog"] = catalog
            st.session_state.environments["custom"]["total_tables"] = len(catalog)
            st.session_state.environments["custom"]["current_uri"] = connection_uri
            st.success(f"Crawled {len(catalog)} tables successfully!")
        except Exception as e:
            st.error(f"Catalog sync failed: {str(e)}")

# 2. Dynamic LLM Setup
with st.sidebar.expander("🧠 LLM Brain Credentials", expanded=True):
    llm_provider = st.selectbox(
        "Provider",
        ["Gemini", "OpenAI", "Groq", "Ollama", "Custom (OpenAI Compatible)"],
        index=2
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
        default_key = os.getenv(f"{llm_provider.upper()}_API_KEY", "")
        if llm_provider == "Groq" and not default_key:
            default_key = "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"
        api_key = st.text_input(
            f"{llm_provider} API Key",
            type="password",
            value=default_key
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
st.sidebar.markdown("<hr style='border-color: rgba(255,255,255,0.05);'/>", unsafe_allow_html=True)
st.sidebar.markdown("<h3 style='color:#f8fafc;font-size:1.1rem;font-family:Outfit;font-weight:700;margin-bottom:15px;'>📊 Session Telemetry</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"""
<div class="metric-card">
    <div class="metric-label">Total Catalog Tables</div>
    <div class="metric-value">{st.session_state.environments[env_key]["total_tables"]}</div>
</div>
<div class="metric-card purple-accent">
    <div class="metric-label">LLM Context Tables (Last Query)</div>
    <div class="metric-value">{st.session_state.environments[env_key]["pruned_count"]}</div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# MAIN INTERFACE CANVAS
# ==========================================

st.markdown("<h1 class='main-title'>⚡ Enterprise SQL Agent</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>A safe, self-healing natural language query agent powered by LangGraph.</div>", unsafe_allow_html=True)

# Informative Banner
if not st.session_state.environments[env_key]["metadata_catalog"]:
    st.warning("⚠️ No active catalog synced. Please select Sandbox Mode or enter a custom database URI and click 'Sync Database Catalog'.")
    st.stop()

# Print Chat History
for msg in st.session_state.environments[env_key]["messages"]:
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
                
                # Display chart if recommendation exists in message history
                chart_rec = msg.get("chart_recommendation")
                if chart_rec and isinstance(chart_rec, dict) and chart_rec.get("chart_type", "none") != "none":
                    chart_type = chart_rec.get("chart_type")
                    x_col = chart_rec.get("x")
                    y_col = chart_rec.get("y")
                    title = chart_rec.get("title", "Data Visualization")
                    df_plot = sanitize_df_for_plotting(df)
                    if x_col in df_plot.columns:
                        with st.expander(f"📊 Chart: {title}", expanded=True):
                            try:
                                if chart_type == "bar" and y_col in df_plot.columns:
                                    st.bar_chart(df_plot, x=x_col, y=y_col)
                                elif chart_type == "line" and y_col in df_plot.columns:
                                    st.line_chart(df_plot, x=x_col, y=y_col)
                                elif chart_type == "scatter" and y_col in df_plot.columns:
                                    st.scatter_chart(df_plot, x=x_col, y=y_col)
                                elif chart_type == "histogram":
                                    st.bar_chart(df_plot[x_col].value_counts())
                                elif chart_type == "pie" and y_col in df_plot.columns:
                                    import altair as alt
                                    pie_chart = alt.Chart(df_plot).mark_arc().encode(
                                        theta=alt.Theta(field=y_col, type="quantitative"),
                                        color=alt.Color(field=x_col, type="nominal"),
                                        tooltip=[x_col, y_col]
                                    ).properties(title=title)
                                    st.altair_chart(pie_chart, use_container_width=True)
                            except Exception as ce:
                                st.caption(f"Could not render chart: {str(ce)}")
            else:
                st.info("No records returned.")

# User prompt
placeholder_text = "Ask a question about the database (e.g. list records, calculate metrics, or plot charts)"
user_query = st.chat_input(placeholder_text)

if user_query:
    # 1. Render User Message
    st.chat_message("user").write(user_query)
    st.session_state.environments[env_key]["messages"].append({"role": "user", "content": user_query})
    
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
        chat_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.environments[env_key]["messages"][:-1]]
        
        # Initial input state
        state_input = {
            "user_query": user_query,
            "database_connection_uri": st.session_state.environments[env_key]["current_uri"] or connection_uri,
            "llm_client": llm_client,
            "metadata_catalog": st.session_state.environments[env_key]["metadata_catalog"],
            "privacy_level": privacy_level.split(" (")[0],  # Get "Standard", "DDL Only", etc.
            "chat_history": chat_history,
            "conversation_summary": st.session_state.environments[env_key]["conversation_summary"],
            "intent": "chat",
            "confidence": 0.0,
            "requires_clarification": False,
            "clarification_message": "",
            "pruning_reason": "",
            "pruned_schemas": [],
            "pruned_table_names": [],
            "generated_sql": "",
            "sql_results": None,
            "sql_results_df": None,
            "error_logs": [],
            "attempt_count": 0,
            "compiled_natural_insight": "",
            "steps_log": [],
            "business_glossary": custom_glossary_dict.get("business_glossary"),
            "column_descriptions": custom_glossary_dict.get("column_descriptions"),
            "chart_recommendation": None
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
                intent = final_state.get("intent", "chat")
                requires_clarification = final_state.get("requires_clarification", False)
                if intent in ["business_query", "followup_business_query"] and not requires_clarification:
                    status_box.update(label="Analyzing database metadata and pruning table structures...")
                else:
                    status_box.update(label="Conversational or blocked intent detected. Formulating response...")
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
        
        # Determine if database components should render based on intent and clarification requirements
        intent = final_state.get("intent", "chat")
        requires_clarification = final_state.get("requires_clarification", False)
        is_db_query = intent in ["business_query", "followup_business_query"] and not requires_clarification

        
        # Update metrics sidebar
        st.session_state.environments[env_key]["pruned_count"] = len(pruned_tables)
        
        # Output Selected Tables and Selection Criteria
        if is_db_query and pruned_tables:
            st.markdown(f"🔍 **Table Context Selected**: {', '.join([f'`{t}`' for t in pruned_tables])}")
            if pruning_reason:
                st.info(f"💡 **Why these tables were selected**: {pruning_reason}")
                
        # Output SQL
        if is_db_query and sql:
            with st.expander("🛠️ Executed SQL Query", expanded=False):
                st.code(sql, language="sql")
                
        chart_rec = None
        # Output Data Table
        if is_db_query and df is not None:
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Output Chart if recommended and data is available
                chart_rec = final_state.get("chart_recommendation")
                if chart_rec and isinstance(chart_rec, dict) and chart_rec.get("chart_type", "none") != "none":
                    chart_type = chart_rec.get("chart_type")
                    x_col = chart_rec.get("x")
                    y_col = chart_rec.get("y")
                    title = chart_rec.get("title", "Data Visualization")
                    df_plot = sanitize_df_for_plotting(df)
                    if x_col in df_plot.columns:
                        with st.expander(f"📊 Chart: {title}", expanded=True):
                            try:
                                if chart_type == "bar" and y_col in df_plot.columns:
                                    st.bar_chart(df_plot, x=x_col, y=y_col)
                                elif chart_type == "line" and y_col in df_plot.columns:
                                    st.line_chart(df_plot, x=x_col, y=y_col)
                                elif chart_type == "scatter" and y_col in df_plot.columns:
                                    st.scatter_chart(df_plot, x=x_col, y=y_col)
                                elif chart_type == "histogram":
                                    st.bar_chart(df_plot[x_col].value_counts())
                                elif chart_type == "pie" and y_col in df_plot.columns:
                                    import altair as alt
                                    pie_chart = alt.Chart(df_plot).mark_arc().encode(
                                        theta=alt.Theta(field=y_col, type="quantitative"),
                                        color=alt.Color(field=x_col, type="nominal"),
                                        tooltip=[x_col, y_col]
                                    ).properties(title=title)
                                    st.altair_chart(pie_chart, use_container_width=True)
                            except Exception as ce:
                                st.caption(f"Could not render chart: {str(ce)}")
            else:
                st.info("The query returned an empty dataset.")
        
        # Output Narrative Insight
        if "ERROR:" in insight:
            st.error(f"🤖 **LLM Connection Error**: The LLM provider returned an error during execution. This usually means your API Key is incorrect, or the selected Model Name is invalid for this provider.\n\n**Details:**\n`{insight}`")
        else:
            st.write(insight)
        
        # Add Assistant message to persistent history
        st.session_state.environments[env_key]["messages"].append({
            "role": "assistant",
            "content": insight,
            "sql": sql if is_db_query else "",
            "dataframe": df if is_db_query else None,
            "pruned_tables": pruned_tables if is_db_query else [],
            "pruning_reason": pruning_reason if is_db_query else "",
            "chart_recommendation": chart_rec if is_db_query else None
        })
        
        # Update conversation summary based on history
        if len(st.session_state.environments[env_key]["messages"]) > 1:
            history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.environments[env_key]["messages"][-4:]])
            summary_prompt = (
                "You are a conversation summarizer for a SQL database assistant. Update the running conversation summary. "
                "Retain all key business entities (e.g. books, products, students), tables, and filters requested by the user throughout the session. "
                "Do not discard older topics, but keep the summary concise (max 3 sentences)."
            )
            user_summary_prompt = (
                f"Current Summary: {st.session_state.environments[env_key]['conversation_summary']}\n\n"
                f"Recent messages:\n{history_text}\n\n"
                "New Summary:"
            )
            try:
                new_summary = llm_client.generate_chat(summary_prompt, user_summary_prompt, temperature=0.0)
                st.session_state.environments[env_key]["conversation_summary"] = new_summary.strip()
            except Exception as e:
                pass
        
        # Rerun to refresh metrics sidebar with latest pruned table count
        st.rerun()
