import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from braintrust import Eval, init_dataset, init_function

from agents.sql_agent import SQLAgent
from prompts.sql_prompt import SQL_SYSTEM_PROMPT

from dotenv import load_dotenv

load_dotenv()

PROJECT = os.environ.get("BRAINTRUST_PROJECT", "agent-evals-workshop")

# Start remote eval server using `braintrust eval eval/eval_sql_agent_remote.py --dev`
# Go playground and select Remote Eval as task


def extract_sql_prompt(sql_prompt_param):
    if not sql_prompt_param:
        return None

    if hasattr(sql_prompt_param, "build"):
        sql_prompt_param = sql_prompt_param.build()

    messages = None
    if hasattr(sql_prompt_param, "messages"):
        messages = sql_prompt_param.messages
    elif isinstance(sql_prompt_param, dict):
        if isinstance(sql_prompt_param.get("messages"), list):
            messages = sql_prompt_param["messages"]
        elif isinstance(sql_prompt_param.get("prompt"), dict):
            messages = sql_prompt_param["prompt"].get("messages")
        elif isinstance(sql_prompt_param.get("default"), dict):
            default_prompt = sql_prompt_param["default"].get("prompt")
            if isinstance(default_prompt, dict):
                messages = default_prompt.get("messages")

    if not isinstance(messages, list):
        return None

    for message in messages:
        if isinstance(message, dict) and message.get("role") == "system":
            content = message.get("content")
            if isinstance(content, str):
                return content

    return None


async def task(input, hooks):

    parameters = hooks.parameters or {}
    sql_prompt = extract_sql_prompt(parameters.get("sql_prompt"))
    
    agent = SQLAgent(system_prompt=sql_prompt)
    result = agent.run(input)
    
    return result

Eval(   
    PROJECT, 
    data=init_dataset(project=PROJECT, name="sql-agent-eval"),
    task=task,
    scores=[init_function(project_name=PROJECT, slug="data_eval"),
            init_function(project_name=PROJECT, slug="sql_eval")],
    max_concurrency=5,
    parameters={
        "sql_prompt": {
            "type": "prompt",
            "name": "SQL Prompt",
            "description": "System prompt to provide context for SQL queries",
            "default": {
                "prompt": {
                    "type": "chat",
                    "messages": [
                        {
                            "role": "system", 
                            "content": SQL_SYSTEM_PROMPT
                        }
                    ],
                },
                "options": {},
            },
        },
    },
)
