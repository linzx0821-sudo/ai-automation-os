from decimal import Decimal, InvalidOperation


class FinancialCalculationError(ValueError):
    pass


def _d(value: Decimal | int | str) -> Decimal:
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise FinancialCalculationError(f"Invalid decimal value: {value}") from exc


def market_cap(price: Decimal | int | str, shares_outstanding: Decimal | int | str) -> Decimal:
    price_d = _d(price)
    shares_d = _d(shares_outstanding)
    if price_d < 0 or shares_d < 0:
        raise FinancialCalculationError("Price and shares outstanding must be non-negative")
    return price_d * shares_d


def net_cash(
    cash_and_equivalents: Decimal | int | str,
    total_debt: Decimal | int | str,
) -> Decimal:
    return _d(cash_and_equivalents) - _d(total_debt)


def price_to_earnings(
    market_cap_value: Decimal | int | str,
    net_income: Decimal | int | str,
) -> Decimal:
    earnings = _d(net_income)
    if earnings <= 0:
        raise FinancialCalculationError("P/E is undefined for non-positive earnings")
    return _d(market_cap_value) / earnings


def free_cash_flow_yield(
    free_cash_flow: Decimal | int | str,
    market_cap_value: Decimal | int | str,
) -> Decimal:
    cap = _d(market_cap_value)
    if cap <= 0:
        raise FinancialCalculationError("Market cap must be positive")
    return _d(free_cash_flow) / cap


def operating_margin(
    operating_income: Decimal | int | str,
    revenue: Decimal | int | str,
) -> Decimal:
    revenue_d = _d(revenue)
    if revenue_d == 0:
        raise FinancialCalculationError("Revenue must be non-zero")
    return _d(operating_income) / revenue_d


def margin_of_safety(
    fair_value: Decimal | int | str,
    current_price: Decimal | int | str,
) -> Decimal:
    fair = _d(fair_value)
    if fair <= 0:
        raise FinancialCalculationError("Fair value must be positive")
    return (fair - _d(current_price)) / fair
