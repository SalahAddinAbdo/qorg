from qorg.qorg.cost_distribution.gl import split_gl_map
class PurchaseInvoiceCostDistributionMixin:
    def get_gl_entries(self, warehouse_account=None):
        return split_gl_map(self,super().get_gl_entries(warehouse_account))
