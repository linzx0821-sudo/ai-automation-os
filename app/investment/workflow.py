import hashlib
import re

from app.investment.schemas import InvestmentResearchPlan, InvestmentResearchRequest


class InvestmentResearchWorkflow:
    def plan(self, request: InvestmentResearchRequest) -> InvestmentResearchPlan:
        identity = " | ".join(
            part for part in (request.company, request.ticker, request.exchange) if part
        )
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:8]
        slug = re.sub(r"[^a-z0-9]+", "-", request.company.lower()).strip("-")[:48] or "company"
        workspace = f"investment/{slug}-{digest}"

        focus = request.focus or "Full company research"
        goal = f"""Investment OS company research task

Target: {identity}
Focus: {focus}

Mission:
Produce an evidence-first investment research package. This is research only. Do not place,
simulate, recommend executing, or automate any brokerage trade.

Required workflow:
1. Resolve the exact listed company/security before using any market or financial data.
2. Build an evidence ledger. Every material factual claim must retain source, publication date,
   reporting period, currency/unit, and confidence.
3. Prefer primary sources: company filings, annual/interim reports, exchange/regulator filings,
   investor relations material, and earnings-call transcripts. Use secondary sources only as
   supplemental evidence.
4. Cross-check key financial figures with a second independent source when practical. If values
   differ materially, preserve both values and investigate instead of silently choosing one.
5. Analyze independently across these functions: business model, moat/competition, financial
   quality, management/capital allocation, industry structure, valuation, long-term risks, and a
   dedicated bearish/red-team case.
6. Separate FACT, INFERENCE, ASSUMPTION, and UNKNOWN. Unknowns must stay unknown; never invent a
   number or citation to complete a template.
7. Do not trust LLM mental arithmetic for investment metrics. Use Python Decimal or an equivalent
   deterministic decimal calculation and preserve inputs/formulas.
8. Run an inversion check: identify concrete scenarios that could invalidate the thesis.
9. Surface disagreements between research functions rather than averaging them away.
10. Finish with a committee-style synthesis that states what is known, what is uncertain, what
    would change the conclusion, and what evidence should be monitored next.

Workspace outputs:
- research/report.md: human-readable research memo.
- research/evidence.json: structured evidence ledger with source metadata and confidence.
- research/metrics.json: deterministic calculated metrics with formula and input provenance.
- research/thesis.json: thesis statements, invalidation conditions, unknowns, and monitor items.

Quality gates:
- No unsupported material factual claim.
- No fabricated source, quote, price, financial figure, or management statement.
- Keep currency and units explicit.
- For time-sensitive facts, record the as-of timestamp.
- If current/reliable data cannot be obtained, state the limitation and stop short of a precise
  valuation conclusion.

Final response:
Summarize completion status, the most important findings, material disagreements/unknowns, and
exact paths of generated workspace artifacts. Do not give an instruction to buy or sell.
"""
        return InvestmentResearchPlan(company=request.company, workspace=workspace, task_goal=goal)
