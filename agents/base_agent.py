"""Base agent class with OpenAI tool-calling loop and Braintrust tracing."""

import json
import os

import braintrust
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Module-level singletons
BRAINTRUST_API_KEY = os.environ.get("BRAINTRUST_API_KEY", "")

client = braintrust.wrap_openai(
    OpenAI(
        base_url="https://api.braintrust.dev/v1/proxy",
        api_key=BRAINTRUST_API_KEY,
    )
)

logger = braintrust.init_logger(project="agent-evals-workshop")


class BaseAgent:
    """Base agent with an OpenAI tool-calling loop."""

    def __init__(self, system_prompt: str, tools: list, model: str = "gpt-5-mini"):
        self.system_prompt = system_prompt
        self.tools = tools
        self.model = model
        self._messages = []

    def execute_tool(self, name: str, args: dict):
        """Execute a tool by name. Override in subclasses."""
        raise NotImplementedError(f"Tool '{name}' not implemented")

    # @braintrust.traced(name="base_agent_run")
    def run(self, user_message: str) -> dict:
        """Run the agent with a user message through the tool-calling loop."""
        if not self._messages:
            self._messages = [{"role": "system", "content": self.system_prompt}]

        self._messages.append({"role": "user", "content": user_message})

        while True:
            response = client.chat.completions.create(
                model=self.model,
                messages=self._messages,
                tools=self.tools if self.tools else None,
            )

            # Validate we got a real response from the LLM
            if not response or not response.choices:
                raise ValueError("No response from LLM - check API configuration")

            message = response.choices[0].message
            self._messages.append(message)

            # If no tool calls, we're done
            if not message.tool_calls:
                return {"response": message.content}

            # Process each tool call
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                with braintrust.start_span(
                    name=func_name,
                    span_attributes={"type": "tool"},
                    input=func_args,
                ) as span:
                    result = self.execute_tool(func_name, func_args)
                    span.log(output=result)

                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })
