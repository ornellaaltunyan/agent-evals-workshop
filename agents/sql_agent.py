"""SQL Agent — queries the NBA database using SQL tools."""

import json

import braintrust

from agents.base_agent import BaseAgent
from prompts.sql_prompt import SQL_SYSTEM_PROMPT
from tools.sql_tools import SQL_TOOLS, run_sql_query, list_tables, describe_table


class SQLAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=SQL_SYSTEM_PROMPT,
            tools=SQL_TOOLS,
            model="gpt-5",
        )
        self._last_sql_query = None

    def execute_tool(self, name: str, args: dict):
        if name == "run_sql_query":
            self._last_sql_query = args["query"]
            return run_sql_query(args["query"])
        elif name == "list_tables":
            return list_tables()
        elif name == "describe_table":
            return describe_table(args["table_name"])
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    @braintrust.traced(name="sql_agent")
    def run(self, user_message: str) -> dict:
        result = super().run(user_message)
        result["sql_query"] = self._last_sql_query
        return result
