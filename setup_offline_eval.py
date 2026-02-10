"""Upload dataset, prompts, and scorers to Braintrust"""

import inspect
import json
import os

from dotenv import load_dotenv

load_dotenv()

import braintrust

from agents.supervisor_agent import SupervisorAgent
from eval.scorers import data_eval
from prompts.sql_prompt import SQL_SYSTEM_PROMPT
from prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT

PROJECT = "agent-evals-workshop"
DATASET_NAME = "sql-agent-eval"


def load_local_dataset():
    dataset_path = os.path.join(os.path.dirname(__file__), "eval", "dataset.json")
    with open(dataset_path) as f:
        return json.load(f)


def delete_dataset(conn):
    resp = conn.get_json("/v1/dataset", {"dataset_name": DATASET_NAME, "project_name": PROJECT})
    for obj in resp.get("objects", []):
        if obj["name"] == DATASET_NAME:
            print(f"Deleting existing dataset '{DATASET_NAME}' ({obj['id']})...")
            conn.delete(f"/v1/dataset/{obj['id']}")
            return
    print(f"No existing dataset '{DATASET_NAME}' found, skipping delete.")


def upload_dataset(conn):
    delete_dataset(conn)
    records = load_local_dataset()
    dataset = braintrust.init_dataset(project=PROJECT, name=DATASET_NAME)
    print(f"Uploading {len(records)} records to dataset '{DATASET_NAME}'...")
    for record in records:
        dataset.insert(
            input=record["input"],
            expected=record.get("expected"),
            metadata=record.get("metadata"),
        )
    dataset.flush()
    print(f"Dataset '{DATASET_NAME}' uploaded.")


def get_project_id(conn):
    resp = conn.get_json("/v1/project", {"project_name": PROJECT})
    for obj in resp.get("objects", []):
        if obj["name"] == PROJECT:
            return obj["id"]
    return None


def upload_prompt(conn, project_id, slug, name, content, model=None):
    print(f"Uploading prompt '{name}'...")
    prompt_data = {
        "prompt": {
            "type": "chat",
            "messages": [{"role": "system", "content": content}],
        }
    }
    if model:
        prompt_data["options"] = {"model": model}
    conn.post_json(
        "/v1/prompt",
        {
            "project_id": project_id,
            "name": name,
            "slug": slug,
            "function_data": {"type": "prompt"},
            "prompt_data": prompt_data,
        },
    )
    print(f"Prompt '{name}' uploaded.")


def upload_code_scorer(conn, project_id, name, slug, func):
    existing = conn.get_json("/v1/function", {"project_name": PROJECT, "slug": slug})
    if existing.get("objects"):
        print(f"Scorer '{name}' already exists, skipping.")
        return
    code = "import re\n\n" + inspect.getsource(func) + f"\n\nhandler = {func.__name__}"
    print(f"Uploading scorer '{name}'...")
    conn.post_json(
        "/v1/function",
        {
            "project_id": project_id,
            "name": name,
            "slug": slug,
            "function_type": "scorer",
            "function_data": {
                "type": "code",
                "data": {
                    "type": "inline",
                    "runtime_context": {
                        "runtime": "python",
                        "version": "3.12",
                    },
                    "code": code,
                },
            },
        },
    )
    print(f"Scorer '{name}' uploaded.")


SQL_EVAL_PROMPT = """\
You are evaluating whether an AI agent's SQL query correctly answers a business question.

User question: {{input}}
Reference SQL: {{metadata.sql_query}}
Agent SQL: {{output.sql_query}}

Score the agent's SQL from 0.0 to 1.0 based on how closely it matches the reference:
- 1.0: Structurally equivalent (same tables, aggregation functions, date ranges, GROUP BY)
- 0.5: Partially correct (some key elements match)
- 0.0: Completely wrong, missing, or does not answer the question

Return JSON with exactly this format:
{
    "score": <float 0-1>,
    "name": "sql_eval",
    "metadata": {
        "rationale": "<brief explanation>"
    }
}
"""


def upload_llm_scorer(conn, project_id, name, slug, prompt, model="gpt-4o-mini"):
    print(f"Uploading LLM scorer '{name}'...")
    conn.post_json(
        "/v1/function",
        {
            "project_id": project_id,
            "name": name,
            "slug": slug,
            "function_type": "scorer",
            "function_data": {"type": "prompt"},
            "prompt_data": {
                "prompt": {
                    "type": "chat",
                    "messages": [{"role": "system", "content": prompt}],
                },
                "options": {
                    "model": model,
                    "params": {"response_format": {"type": "json_object"}},
                },
            },
        },
    )
    print(f"LLM scorer '{name}' uploaded.")


def task(input, hooks=None):
    agent = SupervisorAgent()
    return agent.run(input)


def run():
    braintrust.login()
    conn = braintrust.api_conn()

    upload_dataset(conn)
    project_id = get_project_id(conn)

    upload_prompt(conn, project_id, "sql-system-prompt", "SQL System Prompt", SQL_SYSTEM_PROMPT, model="gpt-5")
    upload_prompt(
        conn,
        project_id,
        "supervisor-system-prompt",
        "Supervisor System Prompt",
        SUPERVISOR_SYSTEM_PROMPT,
        model="gpt-5",
    )
    upload_code_scorer(conn, project_id, "data_eval", "data_eval", data_eval)
    upload_llm_scorer(conn, project_id, "sql_eval", "sql_eval", SQL_EVAL_PROMPT)


if __name__ == "__main__":
    run()
