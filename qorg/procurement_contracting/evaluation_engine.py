from decimal import Decimal
from statistics import pstdev

from .decimal_utils import HUNDRED, decimal, require_exact_hundred, score
from .exceptions import EvaluationError

SUPPORTED_METHODS = {
    "Individual Average",
    "Weighted Member Average",
    "Consensus Score",
    "Individual then Consensus",
    "Individual Pass Fail",
    "Consensus Pass Fail",
    "System Calculated",
    "Single Authorized Assessor",
    "Measured Value to Score",
}


def validate_component_weights(components):
    weighted = [c["weight"] for c in components if c.get("included_in_total", True)]
    return require_exact_hundred(weighted, "component weights")


def validate_criterion_weights(criteria, component):
    weighted = [c["weight"] for c in criteria if c.get("component") == component and c.get("included_in_total", True)]
    if weighted:
        return require_exact_hundred(weighted, f"{component} criterion weights")
    return Decimal("0")


def _eligible_scores(entries):
    return [decimal(e["score"], "score") for e in entries if e.get("submitted") and not e.get("excluded")]


def individual_average(entries, minimum_assessors=1):
    values = _eligible_scores(entries)
    if len(values) < minimum_assessors:
        raise EvaluationError(f"At least {minimum_assessors} eligible submitted assessments are required")
    return score(sum(values) / len(values))


def weighted_member_average(entries):
    eligible = [e for e in entries if e.get("submitted") and not e.get("excluded")]
    if not eligible:
        raise EvaluationError("At least one eligible submitted assessment is required")
    require_exact_hundred([e.get("member_weight", 0) for e in eligible], "member weights")
    value = sum(decimal(e["score"]) * decimal(e["member_weight"]) / HUNDRED for e in eligible)
    return score(value)


def consensus_score(value, quorum_met, rationale):
    if not quorum_met:
        raise EvaluationError("Committee quorum is not met")
    if not str(rationale or "").strip():
        raise EvaluationError("Consensus rationale is required")
    return score(value)


def individual_then_consensus(entries, consensus, quorum_met, rationale, variance_threshold=None):
    average = individual_average(entries)
    final = consensus_score(consensus, quorum_met, rationale)
    values = [float(v) for v in _eligible_scores(entries)]
    dispersion = score(pstdev(values)) if len(values) > 1 else Decimal("0.0000")
    deviation = abs(final - average)
    if variance_threshold is not None and deviation > decimal(variance_threshold):
        if len(str(rationale or "").strip()) < 20:
            raise EvaluationError("A detailed rationale is required when consensus deviates beyond the threshold")
    return {"average": average, "consensus": final, "dispersion": dispersion, "deviation": score(deviation)}


def financial_score(lowest_evaluated_price, bidder_evaluated_price):
    low = decimal(lowest_evaluated_price, "lowest_evaluated_price")
    bid = decimal(bidder_evaluated_price, "bidder_evaluated_price")
    if low <= 0 or bid <= 0:
        raise EvaluationError("Evaluated prices must be greater than zero")
    return score((low / bid) * HUNDRED)


def measured_value_to_score(value, bands):
    measured = decimal(value, "measured value")
    eligible = []
    for band in bands:
        lower = decimal(band["minimum"])
        upper = decimal(band["maximum"])
        if lower <= measured <= upper:
            eligible.append(band)
    if len(eligible) != 1:
        raise EvaluationError("Measured value must match exactly one scoring band")
    return score(eligible[0]["score"])


def weighted_result(raw_score, weight):
    raw = decimal(raw_score, "raw_score")
    w = decimal(weight, "weight")
    if raw < 0 or raw > HUNDRED or w < 0 or w > HUNDRED:
        raise EvaluationError("Scores and weights must be between 0 and 100")
    return score(raw * w / HUNDRED)
