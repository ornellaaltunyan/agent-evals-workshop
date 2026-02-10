"""CLI script to run the NBA analytics agent."""

import sys
import os

from dotenv import load_dotenv

load_dotenv()

from agents.supervisor_agent import SupervisorAgent


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_agent.py \"your question here\"")
        sys.exit(1)

    query = sys.argv[1]
    print(f"Question: {query}\n")

    agent = SupervisorAgent()
    result = agent.run(query)

    print(f"Answer:\n{result['response']}")
    if result.get("sql_query"):
        print(f"\nSQL Query Used:\n{result['sql_query']}")


if __name__ == "__main__":
    main()
