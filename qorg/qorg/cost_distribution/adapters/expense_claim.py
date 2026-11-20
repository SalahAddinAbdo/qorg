from qorg.qorg.cost_distribution.gl import split_gl_map
class ExpenseClaimCostDistributionMixin:
    def get_gl_entries(self):
        return split_gl_map(self,super().get_gl_entries())
