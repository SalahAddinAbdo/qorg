from decimal import Decimal, ROUND_HALF_UP

SCORE_QUANTUM = Decimal("0.0001")
MONEY_QUANTUM = Decimal("0.01")
HUNDRED = Decimal("100")


def decimal(value, field="value"):
    if value is None or value == "":
        raise ValueError(f"{field} is required")
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field} must be numeric") from exc


def score(value):
    return decimal(value).quantize(SCORE_QUANTUM, rounding=ROUND_HALF_UP)


def money(value):
    return decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def require_exact_hundred(values, label="weights"):
    total = sum((decimal(v) for v in values), Decimal("0"))
    if total != HUNDRED:
        difference = HUNDRED - total
        raise ValueError(
            f"{label} must total exactly 100%; current total is {total}% and required difference is {difference}%"
        )
    return total
