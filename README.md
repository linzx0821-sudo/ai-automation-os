# AI Automation OS

AI-first automation platform with Codex as an engineering/execution worker and Investment OS as the first domain app.

## V0.1 goal

Build a durable task pipeline:

1. Create an automation task.
2. Route it through an orchestrator.
3. Delegate executable work to a Codex gateway.
4. Persist task/thread state.
5. Resume the same task safely.
6. Keep auditable logs and approval gates.

## Initial stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Pydantic 2
- OpenAI Agents SDK
- Codex CLI / SDK gateway abstraction
- Pytest
- Docker Compose

## Safety baseline

V0.1 does not place trades or mutate brokerage accounts. High-impact actions require explicit approval gates.
