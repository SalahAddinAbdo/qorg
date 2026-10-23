from __future__ import annotations

from qorg.qorg.enterprise_foundation.policy_enforcement import get_policy_map


def extend_bootinfo(bootinfo):
    bootinfo.qorg_model_policies = get_policy_map()
