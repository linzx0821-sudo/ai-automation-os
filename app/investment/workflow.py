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

Workspace outputs (all required):
- research/report.md: human-readable research memo.
- research/evidence.json: structured evidence ledger.
- research/metrics.json: deterministic calculated metrics.
- research/thesis.json: thesis statements and invalidation/monitor conditions.

Machine-readable contract, schema_version must be "1.0":

research/evidence.json
{{
  "schema_version": "1.0",
  "generated_at": "ISO-8601 timestamp",
  "company": {{
    "name": "...", "ticker": "...", "exchange": "...",
    "country": null, "currency": null, "sector": null, "industry": null,
    "fiscal_year_end": null
  }},
  "documents": [{{
    "key": "stable-local-key", "document_type": "annual_report|exchange_filing|...",
    "source_type": "company_filing|exchange|regulator|...", "title": "...",
    "source_url": "https://...", "published_at": null, "reporting_period": null,
    "content_sha256": null, "metadata": {{}}
  }}],
  "facts": [{{
    "key": "stable-local-key", "metric": "...", "statement": "...",
    "primary_document_key": null, "value_numeric": null, "value_text": null,
    "currency": null, "unit": null, "period_start": null, "period_end": null,
    "as_of": null, "source_quote": null, "source_location": null,
    "confidence": "high|medium|low|unknown",
    "verification_status": "unverified|verified|conflict|insufficient",
    "sources": [{{
      "document_key": "...", "reported_value_numeric": null,
      "reported_value_text": null, "variance_ratio": null,
      "status": "supporting|conflicting|context"
    }}]
  }}]
}}
A fact may have value_numeric OR value_text, never both. All document references must resolve.

research/metrics.json
{{
  "schema_version": "1.0",
  "metrics": [{{
    "metric": "...", "value_numeric": "decimal string", "currency": null,
    "unit": null, "period_end": null, "formula": "...", "formula_version": "1.0",
    "input_fact_keys": ["fact-key"]
  }}]
}}
Every input_fact_key must exist in evidence.json. Never emit a calculated metric without its
formula and input provenance.

research/thesis.json
{{
  "schema_version": "1.0",
  "theses": [{{
    "title": "...", "statement": "...",
    "status": "active|strengthened|weakened|invalidated|unknown",
    "confidence": null, "evidence_fact_keys": ["fact-key"],
    "conditions": [{{
      "condition_type": "strengthen|weaken|invalidate|monitor",
      "description": "...", "metric": null,
      "operator": null, "threshold_numeric": null, "unit": null,
      "consecutive_periods": null
    }}]
  }}]
}}
Every evidence_fact_key must exist in evidence.json. Confidence, when known, is 0..1.

Quality gates:
- No unsupported material factual claim.
- No fabricated source, quote, price, financial figure, or management statement.
- Keep currency and units explicit.
- For time-sensitive facts, record the as-of timestamp.
- JSON files must be valid strict JSON, not Markdown fenced blocks.
- If current/reliable data cannot be obtained, state the limitation and stop short of a precise
  valuation conclusion. Still produce valid artifacts containing the verified evidence available.

Final response:
Summarize completion status, the most important findings, material disagreements/unknowns, and
exact paths of generated workspace artifacts. Do not give an instruction to buy or sell.
"""
        return InvestmentResearchPlan(company=request.company, workspace=workspace, task_goal=goal)
