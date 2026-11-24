import importlib.util
import sys
import types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]

def load_module():
    frappe=types.ModuleType('frappe')
    frappe._=lambda x:x
    frappe.whitelist=lambda *a,**k:(lambda f:f)
    frappe.PermissionError=PermissionError
    frappe.get_roles=lambda:[]
    frappe.session=types.SimpleNamespace(user='test@example.com')
    frappe.utils=types.ModuleType('frappe.utils')
    frappe.utils.add_days=lambda d,n:d
    frappe.utils.flt=lambda x:float(x or 0)
    frappe.utils.getdate=lambda x:x
    frappe.utils.now_datetime=lambda:'2026-01-01 00:00:00'
    frappe.utils.today=lambda:'2026-01-01'
    sys.modules['frappe']=frappe
    sys.modules['frappe.utils']=frappe.utils
    spec=importlib.util.spec_from_file_location('perf_calc',ROOT/'qorg/qorg/employee_lifecycle/performance.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def test_source_score_normalization():
    module=load_module()
    assert module._normalize_source_score(4,5)==80
    assert module._normalize_source_score(5,5)==100

def test_completed_weight_and_reallocation_are_distinct_in_audit_rows():
    source=(ROOT/'qorg/qorg/employee_lifecycle/performance.py').read_text()
    assert 'row["effective_weight"] = flt(row["weight"])' in source
    assert 'row["effective_weight"] = flt(row["weight"]) * 100 / denominator' in source
    assert 'Source Score Maximum' in source

def test_standard_submit_closes_appraisal():
    source=(ROOT/'qorg/qorg/employee_lifecycle/performance.py').read_text()
    assert 'Appraisal must be Finalized before submission' in source
    assert '"qorg_stage": "Closed"' in source
