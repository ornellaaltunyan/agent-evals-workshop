"""Supervisor Agent — delegates data questions to the SQL Agent."""

import json

import braintrust

from agents.base_agent import BaseAgent
from agents.sql_agent import SQLAgent
from prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT

SUPERVISOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ask_sql_agent",
            "description": "Ask the SQL agent to query the NBA database. Provide a clear natural language question about the data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The data question to answer using SQL.",
                    }
                },
                "required": ["question"],
            },
        },
    }
]


class SupervisorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
            tools=SUPERVISOR_TOOLS,
            model="gpt-5",
        )
        self._last_sql_query = None

    def execute_tool(self, name: str, args: dict):
        if name == "ask_sql_agent":
            sql_agent = SQLAgent()
            result = sql_agent.run(args["question"])
            self._last_sql_query = result.get("sql_query")
            return result["response"]
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    @braintrust.traced(name="supervisor_agent")
    def run(self, user_message: str) -> dict:
        result = super().run(user_message)
        result["sql_query"] = self._last_sql_query
        return result
