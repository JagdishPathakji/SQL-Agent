import logging
from typing import Dict, Any
from sqlalchemy import create_engine, inspect
from .glossary import SEMANTIC_COLUMN_DESCRIPTIONS

logger = logging.getLogger(__name__)

def crawl_database_metadata(connection_uri: str) -> Dict[str, Any]:
    """Crawls database tables, columns, constraints and schema to construct a fast in-memory catalog."""
    logger.info("Running Metadata Crawler on connected database...")
    engine = create_engine(connection_uri)
    inspector = inspect(engine)
    catalog = {}
    
    try:
        table_names = inspector.get_table_names()
        for tbl in table_names:
            try:
                cols = []
                for col in inspector.get_columns(tbl):
                    cols.append({
                        "name": col["name"],
                        "type": str(col["type"]),
                        "primary_key": 1 if col.get("primary_key", False) else 0,
                        "nullable": col.get("nullable", True),
                        "default": str(col.get("default")) if col.get("default") else None,
                        "comment": col.get("comment", "")
                    })
                
                fkeys = []
                for fk in inspector.get_foreign_keys(tbl):
                    fkeys.append({
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"]
                    })
                    
                catalog[tbl] = {
                    "columns": cols,
                    "foreign_keys": fkeys,
                    "description": f"Table containing information about {tbl.replace('_', ' ')}."
                }
            except Exception as table_err:
                logger.warning(f"Skipping table {tbl} due to crawl error: {table_err}")
        logger.info(f"Crawl completed. Extracted metadata catalog for {len(catalog)} tables.")
    except Exception as e:
        logger.error(f"Error crawling database metadata: {e}")
        raise e
    finally:
        engine.dispose()
        
    return catalog

def compile_ddl(table_name: str, table_meta: Dict[str, Any], column_descriptions: Dict[str, str] = None) -> str:
    """Compiles a CREATE TABLE statement based on table metadata, injecting semantic glossary comments."""
    ddl_lines = []
    col_descs = column_descriptions if column_descriptions is not None else SEMANTIC_COLUMN_DESCRIPTIONS
    for col in table_meta["columns"]:
        line = f"  {col['name']} {col['type']}"
        if col["primary_key"]:
            line += " PRIMARY KEY"
        if not col["nullable"]:
            line += " NOT NULL"
        if col["default"]:
            line += f" DEFAULT {col['default']}"
            
        # Lookup semantic column description
        glossary_key = f"{table_name}.{col['name']}"
        comment = col.get("comment", "")
        if glossary_key in col_descs:
            semantic_desc = col_descs[glossary_key]
            comment = f"{semantic_desc} | {comment}" if comment else semantic_desc
            
        if comment:
            line += f" -- Description: {comment}"
        ddl_lines.append(line)
        
    for fk in table_meta["foreign_keys"]:
        line = f"  FOREIGN KEY ({', '.join(fk['constrained_columns'])}) REFERENCES {fk['referred_table']} ({', '.join(fk['referred_columns'])})"
        ddl_lines.append(line)
        
    return f"CREATE TABLE {table_name} (\n" + ",\n".join(ddl_lines) + "\n);"
