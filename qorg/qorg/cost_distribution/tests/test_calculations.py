from types import SimpleNamespace
from qorg.qorg.cost_distribution.calculations import calculate_targets
def test_fixed_percentage_rounding():
 p=SimpleNamespace(distribution_method="Fixed Percentage",difference_handling="Allocate Rounding Difference",targets=[SimpleNamespace(allow_distribution=1,allocation_percentage=50),SimpleNamespace(allow_distribution=1,allocation_percentage=50)])
 rows=calculate_targets(p,100,100);assert sum(x["allocated_amount"] for x in rows)==100
