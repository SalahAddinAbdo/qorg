from qorg.qorg.cost_distribution.gl import split_gl_map


class PurchaseInvoiceCostDistributionMixin:
    def get_gl_entries(self, inventory_account_map=None):
        return split_gl_map(self, super().get_gl_entries(inventory_account_map))
