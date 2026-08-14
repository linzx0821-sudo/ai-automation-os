# AGENTS.md

## Mission
Build AI Automation OS as a durable, auditable automation platform. Codex is an execution worker, not an unsupervised authority.

## V0.1 priorities
1. Durable task state in PostgreSQL.
2. Real Codex adapter with thread start/resume.
3. Structured run/event logs.
4. Approval gates for high-impact actions.
5. Investment OS as the first workflow pack.

## Engineering rules
- Prefer typed Python and small modules.
- Critical calculations must be deterministic and testable outside the LLM.
- Never silently fabricate tool outputs, IDs, data, or citations.
- Preserve task/thread IDs so work can resume.
- High-impact external writes must pass an approval policy.
- Add tests with every behavior change.
- Keep secrets in environment variables; never commit credentials.

## Definition of done
A change is done only when its tests pass and failures are surfaced explicitly.
