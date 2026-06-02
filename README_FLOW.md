# Code Flow & Debugging Guide: SQL-Agent

This guide outlines the execution flow of the **Enterprise SQL Agent** codebase. Use this to trace variables, debug node states, and understand the role of each module during runtime.

---

## 📂 Architecture Map

The project contains four core components:

1. **[app.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/app.py)**: Streamlit frontend. It gathers user input, initializes parameters, invokes the LangGraph stream, and renders progress/results.
2. **`database/`**: Database setup, cataloging, & schemas.
   - **[database/glossary.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/database/glossary.py)**: Holds `BUSINESS_GLOSSARY` and `SEMANTIC_COLUMN_DESCRIPTIONS`.
   - **[database/crawler.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/database/crawler.py)**: Holds `crawl_database_metadata` and the schema compiler `compile_ddl`.
   - **[database/sandbox.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/database/sandbox.py)**: Holds `generate_college_erp_db` (ERP tables creation & sample inserts).
3. **`llm/`**: Unified API wrapper.
   - **[llm/client.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/llm/client.py)**: Houses the `LLMClient` API wrapper.
4. **`agent/`**: LangGraph orchestrator.
   - **[agent/state.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/agent/state.py)**: Defines `AgentState` schema dictionary.
   - **[agent/router.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/agent/router.py)**: Houses conditional routing logics (`route_intent`, `route_execution`).
   - **[agent/graph.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/agent/graph.py)**: Wires nodes & conditional edges, and compiles the graph.
   - **`agent/nodes/`**: Individual steps in the workflow:
     - **[intent.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/agent/nodes/intent.py)**: Implements `intent_classifier_node`.
     - **[pruner.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/agent/nodes/pruner.py)**: Implements `metadata_pruner_node`.
     - **[generator.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/agent/nodes/generator.py)**: Implements `sql_generation_node`.
     - **[executor.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/agent/nodes/executor.py)**: Implements `security_and_execution_node`.
     - **[synthesizer.py](file:///c:/Users/patha/OneDrive/Desktop/SQL-Agent/agent/nodes/synthesizer.py)**: Implements `insight_synthesis_node`.

---

## 🔄 Execution Flow Tracing (By Case Scenario)

Here is how variables pass through the codebase in four different scenarios.

---

### Case 1: Standard DB Query (Needs DB Access)
*Example: "Find the average grade of active students in Turing Hall"*

1. **Input Submission (`app.py`)**
   - The user inputs the query. Streamlit captures `user_query` and invokes the compiled LangGraph workflow.
2. **Intent Classification (`agent/nodes/intent.py`)**
   - Streamlit invokes `intent_classifier_node()`.
   - The user query is classified as a database query.
   - **Returned State Update**: `{"is_db_query": True}`.
   - **Router Action**: `route_intent()` (in `agent/router.py`) inspects state and redirects execution to `metadata_pruner_node`.
3. **Table Selector / Pruning (`agent/nodes/pruner.py`)**
   - `metadata_pruner_node()` runs.
   - The LLM receives the `BUSINESS_GLOSSARY` (from `database/glossary.py`) and prunes the 22 tables.
   - It selects tables: `students`, `hostel_allotments`, `hostels`, `enrollments`, `grades`.
   - **Returned State Update**:
     - `pruned_table_names`: `["students", "hostel_allotments", "hostels", "enrollments", "grades"]`
     - `pruned_schemas`: Created by calling `compile_ddl()` in `database/crawler.py` for each selected table.
4. **SQL Code Generation (`agent/nodes/generator.py`)**
   - `sql_generation_node()` runs.
   - The LLM is prompted with the pruned schemas.
   - It generates the SQL query:
     ```sql
     SELECT AVG(g.marks_obtained) FROM students s JOIN hostel_allotments ha ON s.student_id = ha.student_id JOIN hostels h ON ha.hostel_id = h.hostel_id JOIN enrollments e ON s.student_id = e.student_id JOIN grades g ON e.enrollment_id = g.enrollment_id WHERE s.status = 'Active' AND h.hostel_name = 'Turing Hall'
     ```
   - **Returned State Update**: `{"generated_sql": "SELECT ...", "attempt_count": 1}`.
5. **Execution & Validation (`agent/nodes/executor.py`)**
   - `security_and_execution_node()` runs.
   - A regex check ensures no write operations (`DROP`, `DELETE`) are attempted, and verifies `sqlite_master` isn't queried.
   - The query executes locally via SQLAlchemy.
   - **Returned State Update**: `{"sql_results": [...], "sql_results_df": pd.DataFrame}`.
6. **Insight Synthesis (`agent/nodes/synthesizer.py`)**
   - `insight_synthesis_node()` runs.
   - If **Standard Mode** is active: Sends the query results data directly to `llm/client.py` to write a natural explanation.
   - If **Strict Privacy Mode** is active: The LLM writes a compliance summary explaining *what* was queried, while the dataframe is printed locally on the UI.
   - **Returned State Update**: `{"compiled_natural_insight": "The average grade obtained is..."}`.
7. **UI Output Rendering (`app.py`)**
   - Streamlit prints the table context selection card, the SQL code block, the pandas dataframe, and the narrative insight.

---

### Case 2: General/Conversational Query (No DB Access)
*Example: "Hello! Who are you?"*

1. **Input Submission (`app.py`)**
   - Captured string: `"Hello! Who are you?"`.
2. **Intent Classification (`agent/nodes/intent.py`)**
   - `intent_classifier_node()` runs.
   - The classifier prompt detects chitchat/general greetings.
   - **Returned State Update**:
     - `is_db_query`: `False`
     - `compiled_natural_insight`: `"Hello! I am your database assistant. How can I help you query the database today?"`
3. **Router Action (`agent/router.py`)**
   - `route_intent()` checks `state["is_db_query"]`.
   - Since it is `False`, it routes directly to `insight_synthesis_node` (bypassing table selection, SQL generation, and database execution entirely).
4. **Insight Synthesis (`agent/nodes/synthesizer.py`)**
   - `insight_synthesis_node()` runs, detects that `is_db_query` is `False`, and finishes.
5. **UI Rendering (`app.py`)**
   - Streamlit displays the conversational response immediately. No database loader or SQL schema selectors are shown.

---

### Case 3: Blocked / Sensitive Query
*Example: "How many tables are in the database?" or "DROP TABLE staff;"*

1. **Input Submission (`app.py`)**
   - Captured string: `"How many tables are in the database?"`.
2. **Intent Classifier Interception (`agent/nodes/intent.py`)**
   - Prior to sending the query to the LLM, regex pattern matchers scan for catalog structures (e.g. `sqlite_master`, `information_schema`, `how many tables`).
   - The query matches the metadata/schema catalog pattern.
   - **Returned State Update**:
     - `is_db_query`: `False`
     - `compiled_natural_insight`: `"I am configured to answer business questions about Academic Administrations, Financial Ledgers, and Hostel Records. I cannot provide internal database structures, table schemas, or column definitions for security reasons."`
   - **Execution Pathway**: Routes immediately to `insight_synthesis_node` and halts, keeping internal table list or metadata logs secure.

*Alternative: The query bypasses classification but attempts a write statement: "DROP TABLE staff"*
1. **Node Transitions**: Classified as a query -> Pruned -> SQL Generated as `DROP TABLE staff`.
2. **Security Audit (`agent/nodes/executor.py`)**:
   - `security_and_execution_node()` scans the SQL string.
   - Finds forbidden keyword `DROP`.
   - Blocks database transaction.
   - **Returned State Update**:
     - Adds `{"sql": "DROP TABLE staff", "error": "Security Violation: Forbidden keyword 'DROP' detected."}` to `error_logs`.
     - `sql_results` remains `None`.
3. **Synthesis**:
   - `insight_synthesis_node()` reads the last error and prints a warning banner on the screen: *"Unable to answer the question due to database execution failure: Security Violation: Forbidden keyword 'DROP' detected."*

---

### Case 4: SQL Execution Error & Self-Healing
*Example: Querying "teachers and their role" where the generator writes `c.course_name` instead of the actual column `c.course_title`.*

1. **Initial Flow**: Node A classifies intent -> Node B prunes schema -> Node C generates SQL.
2. **SQL Generation (`agent/nodes/generator.py`)**:
   - LLM writes query:
     ```sql
     SELECT i.first_name, c.course_name FROM instructors i JOIN sections s ON i.instructor_id = s.instructor_id JOIN courses c ON s.course_id = c.course_id
     ```
3. **Execution Failure (`agent/nodes/executor.py`)**:
   - `security_and_execution_node()` attempts database transaction.
   - SQLite returns `OperationalError: no such column: c.course_name`.
   - **Returned State Update**:
     - `sql_results` set to `None`.
     - `error_logs`: `[{"sql": "SELECT ...", "error": "no such column: c.course_name"}]`.
4. **Conditional Router (`agent/router.py`)**:
   - `route_execution()` runs.
   - Checks that `sql_results` is `None` and `attempt_count` (currently `1`) is less than `3`.
   - **Reroute Decision**: Routes execution back to `sql_generation_node`.
5. **Self-Healing Generation (`agent/nodes/generator.py`)**:
   - `sql_generation_node()` runs for Attempt 2.
   - Prompt includes the `### Previous Execution Errors` section containing the failed query and the `no such column: c.course_name` traceback.
   - The LLM inspects the DDL, notices the column is `course_title`, and rewrites the query:
     ```sql
     SELECT i.first_name, c.course_title FROM instructors i JOIN sections s ON i.instructor_id = s.instructor_id JOIN courses c ON s.course_id = c.course_id
     ```
6. **Re-Execution Success**:
   - `security_and_execution_node()` runs.
   - Executed successfully.
   - **Returned State Update**: `{"sql_results": [...], "sql_results_df": pd.DataFrame}`.
7. **Reroute Decision**:
   - `route_execution()` sees `sql_results` is not `None` and routes to `insight_synthesis_node`.
8. **Completion**:
   - Insights synthesized and results rendered cleanly on Streamlit.
