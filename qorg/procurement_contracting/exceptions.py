class ProcurementError(Exception):
    """Base procurement exception."""


class ConfigurationError(ProcurementError):
    """Invalid or ambiguous configuration."""


class PolicyResolutionError(ProcurementError):
    """No deterministic procurement policy can be resolved."""


class EvaluationError(ProcurementError):
    """Invalid evaluation input or calculation."""


class CommitteeError(ProcurementError):
    """Committee mandate or quorum is invalid."""
