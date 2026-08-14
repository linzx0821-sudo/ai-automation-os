# AGENTS.md

## Mission
Build AI Automation OS as a durable, auditable automation platform. Codex is an execution worker, not an unsupervised authority.

## V0.1 priorities
1. Durable task state in PostgreSQL.
2. Real Codex adapter with thread start/resume.
3. Structured run/event logs and indexed artifacts.
4. Approval gates for high-impact actions.
5. Investment OS as the first workflow pack.
6. Durable queued/background execution for long-running automations.

## Core execution boundary
- Codex owns execution: code, workspace operations, evidence collection, deterministic data preparation.
- Domain agents own reasoning over supplied evidence; they must not invent or silently fetch extra facts.
- Committee agents synthesize specialist outputs and preserve material disagreements.
- Deterministic calculations own critical numbers. LLM mental arithmetic is not authoritative.
- Database memory owns durable facts, metrics, theses and task state.

## Investment OS rules
- Codex produces `research/evidence.json`, `research/metrics.json` and collection notes.
- Investment specialist agents consume only the validated evidence ledger and deterministic metrics.
- A claim marked as fact must cite a valid evidence fact key.
- `FACT`, `INFERENCE`, `ASSUMPTION` and `UNKNOWN` must remain distinct.
- Evidence conflicts and unknowns must be preserved, not averaged away.
- Final report/thesis artifacts come from the Committee layer, not the evidence collector.
- Research artifacts must pass strict schemas before durable memory import.
- V0.1 does not place trades, mutate brokerage accounts or instruct automated execution of securities transactions.

## Engineering rules
- Prefer typed Python and small modules.
- Critical calculations must be deterministic and testable outside the LLM.
- Never silently fabricate tool outputs, IDs, data, prices, sources, citations, or management statements.
- Preserve task/thread IDs so work can resume.
- High-impact external writes must pass an approval policy.
- Workspace paths must stay inside configured roots; never trust caller-provided absolute paths.
- Index artifacts safely; exclude secrets and credentials.
- Add tests with every behavior change.
- Keep secrets in environment variables or a deployment secret store; never commit credentials.

## Definition of done
A change is done only when lint, migrations and tests pass and failures are surfaced explicitly.
