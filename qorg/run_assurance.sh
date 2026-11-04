#!/usr/bin/env bash
set -euo pipefail
SITE="${1:-erpq.erpq.net}"
bench --site "$SITE" run-tests --module qorg.qorg.design_system.test_design_system
bench --site "$SITE" run-tests --module qorg.qorg.enterprise_foundation.tests.test_managed_configuration_state
bench --site "$SITE" run-tests --module qorg.qorg.enterprise_foundation.tests.test_writer_inventory
bench --site "$SITE" run-tests --module qorg.qorg.enterprise_foundation.tests.test_legacy_integrity
bench --site "$SITE" run-tests --module qorg.qorg.enterprise_foundation.tests.test_foundation_permissions
bench --site "$SITE" run-tests --module qorg.qorg.enterprise_foundation.tests.test_workflow_responsibility
