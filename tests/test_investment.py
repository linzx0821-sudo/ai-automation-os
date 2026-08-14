from fastapi.testclient import TestClient

from app.main import app


def test_investment_research_creates_evidence_first_codex_task() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/investment/research",
            json={
                "company": "Tencent Holdings",
                "ticker": "0700",
                "exchange": "HKEX",
                "focus": "Long-term business quality and valuation readiness",
            },
        )

    assert response.status_code == 200
    task = response.json()
    assert task["status"] == "completed"
    assert task["workspace"].startswith("investment/tencent-holdings-")
    assert "evidence-collection worker" in task["goal"].lower()
    assert "Do not place" in task["goal"]
    assert "Python Decimal" in task["goal"]
    assert "Do NOT generate research/thesis.json" in task["goal"]
    assert task["approval_required"] is False
