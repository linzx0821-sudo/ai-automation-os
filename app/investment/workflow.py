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
        goal = f"""Investment OS evidence-collection task

Target: {identity}
Focus: {focus}

Your role:
You are the execution and evidence-collection worker, not the investment committee. Collect,
normalize, verify, and calculate. A separate multi-agent reasoning layer will analyze your outputs.
This is research only. Do not place, simulate, recommend executing, or automate a brokerage trade.

Required workflow:
1. Resolve the exact listed company/security before using market or financial data.
2. Collect primary evidence first: company filings, annual/interim reports, regulator/exchange
   filings, investor-relations materials and earnings-call materials. Secondary sources may only
   supplement primary evidence.
3. Build a fact ledger. Every material fact must retain source URL, publication/reporting date,
   currency/unit, source location when available, and confidence.
4. Cross-check key financial values with a second independent source when practical. If two values
   materially disagree, preserve the conflict rather than silently choosing one.
5. Never fabricate a source, quote, price, financial value, management statement, or date.
6. Do not use LLM mental arithmetic for financial metrics. Use Python Decimal or an equivalent
   deterministic decimal implementation. Preserve formulas and input fact keys.
7. Keep FACT and UNKNOWN distinct. Do not write investment theses or a buy/sell recommendation.
8. For time-sensitive values, record an explicit as-of timestamp.

Workspace outputs required from Codex:
- research/evidence.json: normalized source documents and fact ledger.
- research/metrics.json: deterministic calculated metrics with formula/input provenance.
- research/collection_notes.md: collection limitations, source conflicts and unresolved data gaps.

Do NOT generate research/thesis.json or the final research/report.md. The downstream Investment
Agents and Committee own those outputs.

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
A fact may have value_numeric OR value_text, never both. Every document reference must resolve.

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

Quality gates:
- No unsupported material factual claim.
- No fabricated citation or numeric value.
- Currency and units must be explicit.
- JSON must be strict JSON, not Markdown fenced blocks.
- If reliable current data is unavailable, record the gap and do not invent a substitute.

Final response:
Report only collection completion, important source conflicts/data gaps, and the exact artifact
paths. Do not provide an investment conclusion or transaction instruction.
"""
        return InvestmentResearchPlan(company=request.company, workspace=workspace, task_goal=goal)
