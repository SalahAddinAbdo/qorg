import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def test_contract_doctypes_parse_and_have_controllers():
    for name in ("qorg_contract_type", "contract_amendment"):
        base = ROOT / "qorg" / "qorg" / "doctype" / name
        data = json.loads((base / f"{name}.json").read_text())
        assert data["doctype"] == "DocType"
        assert (base / f"{name}.py").exists()


def test_unified_contract_hooks_are_registered_once():
    module = ast.parse((ROOT / "qorg" / "hooks.py").read_text())
    assignments = {node.targets[0].id: node.value for node in module.body if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
    doc_events = ast.literal_eval(assignments["doc_events"])
    assert "qorg.qorg.unified_contracts.services.validate_contract" in str(doc_events["Contract"]["validate"])
    values = doc_events["Contract"]["validate"]
    assert "qorg.qorg.procurement_contracting.contract_engine.validate_contract" in values
    assert "qorg.qorg.unified_contracts.services.validate_contract" in values
    assert "Procurement Contract" not in doc_events



def test_retired_procurement_contract_has_no_runtime_registration():
    hooks = (ROOT / "qorg" / "hooks.py").read_text()
    assert "'Procurement Contract':" not in hooks
    assert not (ROOT / "qorg" / "qorg" / "doctype" / "procurement_contract").exists()


def test_buying_links_target_unified_contract():
    for relative in (
        "qorg/qorg/procurement_contracting/provisioning.py",
        "qorg/qorg/inventory_asset_custody/custom_fields.py",
    ):
        text = (ROOT / relative).read_text()
        assert "custom_procurement_contract" in text
        assert "'Contract'" in text or '"Contract"' in text
