"""SQL tools for querying the NBA SQLite database."""

import json
import os
import re
import sqlite3

import braintrust

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nba.db")


# @braintrust.traced(name="run_sql_query")
def run_sql_query(query: str, input_message: str = "") -> str:
    """Execute a SQL query and return results as a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = [dict(row) for row in cur.fetchall()]
        return json.dumps(rows, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# @braintrust.traced(name="list_tables")
def list_tables() -> str:
    """List all tables in the database."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall()]
        return json.dumps(tables)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# @braintrust.traced(name="describe_table")
def describe_table(table_name: str) -> str:
    """Describe the schema of a table."""
    # Sanitize table name to prevent SQL injection
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        return json.dumps({"error": "Invalid table name"})

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cur.fetchall():
            columns.append({
                "name": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "primary_key": bool(row[5]),
            })
        return json.dumps(columns)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# OpenAI function-calling tool definitions
SQL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": "Execute a SQL query against the NBA database and return results as JSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute.",
                    },
                    "input_message": {
                        "type": "string",
                        "description": "The original user question this query is answering.",
                    },
                },
                "required": ["query", "input_message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all tables in the NBA database.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": "Get the schema (columns, types) of a specific table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the table to describe.",
                    }
                },
                "required": ["table_name"],
            },
        },
    },
]
