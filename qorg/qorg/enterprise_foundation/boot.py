from qorg.qorg.enterprise_foundation.model_policy_engine import active_action_policies
from qorg.qorg.enterprise_foundation.policy_enforcement import get_policy_map
def extend_bootinfo(bootinfo):
 bootinfo.qorg_model_policies=get_policy_map(); bootinfo.qorg_action_policies=active_action_policies()
