import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def test_standard_skill_models_are_projected_not_replaced():
 source=(ROOT/'qorg/qorg/employee_lifecycle/development.py').read_text()
 for token in ('Employee Skill Map','Designation Skill','skill_gaps','create_gap_actions'):assert token in source
 assert not (ROOT/'qorg/qorg/doctype/employee_skill_map').exists()
 assert not (ROOT/'qorg/qorg/doctype/skill_assessment').exists()
def test_development_actions_are_idempotent():
 source=(ROOT/'qorg/qorg/employee_lifecycle/development.py').read_text()
 assert 'duplicate = frappe.db.get_value("Development Action"' in source
 assert '"existing": existing' in source
def test_recommendations_prepare_standard_execution_documents():
 source=(ROOT/'qorg/qorg/employee_lifecycle/development.py').read_text()
 for token in ('Employee Promotion','Employee Transfer','Salary Structure Assignment','Contract Amendment','Workforce Funding Plan','Development Action'):assert token in source
 assert 'Recommendations can be prepared only after the Appraisal is Finalized' in source
def test_history_is_projection_not_new_history_doctype():
 source=(ROOT/'qorg/qorg/employee_lifecycle/history.py').read_text()
 assert 'Read-only projection' in source
 assert not (ROOT/'qorg/qorg/doctype/development_history').exists()
 for token in ('Training Assessment','Training Follow-up','Appraisal','Employee Promotion','Employee Document Record'):assert token in source
def test_setup_extends_standard_skill_and_appraisal_models():
 setup=(ROOT/'qorg/qorg/employee_lifecycle/dev_setup.py').read_text()
 for token in ('Designation Skill','Skill Assessment','Employee Skill','Appraisal','qorg_required_level','qorg_development_action'):assert token in setup
 assert 'field_order' not in setup and 'Property Setter' not in setup
def test_employee_and_appraisal_clients_are_registered():
 hooks=(ROOT/'qorg/hooks.py').read_text();ast.parse(hooks)
 assert 'employee_dev.js' in hooks and 'setup_development' in hooks
 js=(ROOT/'qorg/public/js/employee_dev.js').read_text();assert 'Skill Gaps' in js and 'Development History' in js
 appraisal=(ROOT/'qorg/public/js/appraisal_ext.js').read_text();assert 'Prepare Recommendation' in appraisal
