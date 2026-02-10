# Agent Evals Workshop

Build and evaluate a multi-agent NBA analytics system with [Braintrust](https://braintrust.dev).

## Architecture

```
User Question
      │
      ▼
┌─────────────┐
│  Supervisor  │  (interprets question, formats response)
│    Agent     │
└──────┬──────┘
       │  ask_sql_agent
       ▼
┌─────────────┐
│  SQL Agent   │  (writes & executes SQL queries)
└──────┬──────┘
       │  run_sql_query / list_tables / describe_table
       ▼
┌─────────────┐
│   SQLite DB  │  (synthetic NBA 2024-25 season data)
└─────────────┘
```

- **Supervisor Agent** — understands basketball analytics questions and delegates to the SQL agent
- **SQL Agent** — translates questions into SQL, executes queries, returns results
- **Braintrust AI Proxy** — all LLM calls route through `api.braintrust.dev/v1/proxy` for automatic tracing
- **Braintrust Eval** — offline eval suite with custom scorers

## Prerequisites

- Python 3.10+
- A [Braintrust](https://braintrust.dev) account and API key

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/your-org/agent-evals-workshop.git
   cd agent-evals-workshop
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up your environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your BRAINTRUST_API_KEY
   ```

4. Generate the synthetic database:
   ```bash
   python setup_db.py
   ```

## Running the agent

Ask any NBA analytics question:

```bash
python run_agent.py "Who scored the most points this season?"
python run_agent.py "Which team has the most wins this season?"
python run_agent.py "Which player averages the most assists per game?"
```

Traces appear automatically in [Braintrust Logs](https://www.braintrust.dev).

## Workshop

### Option 1: Online scoring

Run the agent and inspect traces in the Braintrust UI. Add online scorers directly in the Braintrust dashboard to evaluate responses in real time.

### Option 2: Offline eval

Run the full eval suite with custom scorers:

```bash
python run_eval.py
```

This runs 12 eval cases through the agent and scores each with:
- **data_eval** — checks if correct numeric and string values appear in the response
- **sql_eval** — checks structural similarity of the generated SQL vs. reference SQL

Results appear in the Braintrust Experiments view.

## Project structure

```
agent-evals-workshop/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── setup_db.py                  # Generate SQLite DB with synthetic NBA data
├── run_agent.py                 # Invoke agent with a query
├── run_eval.py                  # Run Braintrust eval
├── agents/
│   ├── base_agent.py            # Base agent: OpenAI tool-calling loop + tracing
│   ├── sql_agent.py             # SQL agent with DB tools
│   └── supervisor_agent.py      # Supervisor that delegates to SQL agent
├── tools/
│   └── sql_tools.py             # run_sql_query, list_tables, describe_table
├── eval/
│   ├── dataset.json             # 12 eval cases with ground truth
│   └── scorers.py               # data_eval + sql_eval scorers
├── data/
│   └── nba.db                   # Generated SQLite DB (gitignored)
└── prompts/
    ├── supervisor_prompt.py
    └── sql_prompt.py
```

## Database schema

The database covers the 2024-25 NBA season (Oct 22, 2024 – Jan 14, 2025) with synthetic data (real team names, fake players and game results).

| Table | Description |
|-------|-------------|
| `teams` | All 30 NBA teams with conference, division, and arena |
| `players` | 450 players (15 per team) with position, college, draft info |
| `games` | 598 games with scores, attendance, and overtime info |
| `rosters` | Player-team assignments for the 2024-25 season |
| `player_game_stats` | Full box score per player per game |
| `team_game_stats` | Team-level aggregates per game (FG%, 3P%, FT%) |
| `seasons` | Season date ranges |

## Sample queries

| Question | What it tests |
|----------|--------------|
| Who scored the most points this season? | SUM aggregation, JOIN, ORDER BY |
| Which team has the most wins this season? | Conditional counting, JOIN |
| What is the average team score per game? | AVG aggregation |
| Which player averages the most assists per game? | AVG with HAVING for min games |
| How many games went to overtime? | Filtered COUNT |
| Which conference has more wins this season? | Multi-table JOIN, GROUP BY |
