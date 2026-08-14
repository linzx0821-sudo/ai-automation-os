from decimal import Decimal

import pytest

from app.investment.financial_calc import (
    FinancialCalculationError,
    free_cash_flow_yield,
    margin_of_safety,
    market_cap,
    net_cash,
    operating_margin,
    price_to_earnings,
)


def test_decimal_financial_metrics_are_exact() -> None:
    cap = market_cap("12.50", "1000000")
    assert cap == Decimal("12500000.00")
    assert net_cash("500", "125") == Decimal("375")
    assert price_to_earnings(cap, "625000") == Decimal("20.00")
    assert free_cash_flow_yield("1000000", cap) == Decimal("0.08")
    assert operating_margin("250", "1000") == Decimal("0.25")
    assert margin_of_safety("100", "75") == Decimal("0.25")


def test_invalid_denominators_are_rejected() -> None:
    with pytest.raises(FinancialCalculationError):
        price_to_earnings("100", "0")
    with pytest.raises(FinancialCalculationError):
        free_cash_flow_yield("10", "0")
    with pytest.raises(FinancialCalculationError):
        operating_margin("10", "0")
