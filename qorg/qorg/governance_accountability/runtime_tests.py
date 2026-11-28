from __future__ import annotations

import frappe


def run_runtime_smoke_tests():
    required_doctypes = (
        'Accountability Case','Investigation Case','Corrective Action','Enterprise Risk',
        'Compliance Obligation','Assurance Finding','Accountability Settings',
    )
    result={'ok':True,'checks':{},'errors':[]}
    for name in required_doctypes:
        exists=bool(frappe.db.exists('DocType',name)); result['checks'][f'doctype:{name}']=exists
        if not exists: result['errors'].append(f'Missing DocType: {name}')
    if frappe.db.exists('Workspace','Governance Accountability'):
        workspace=frappe.get_doc('Workspace','Governance Accountability')
        result['checks']['workspace_module']=workspace.module=='QOrg'
        result['checks']['workspace_public']=bool(workspace.public)
    else:
        result['checks']['workspace_exists']=False; result['errors'].append('Missing Workspace: Governance Accountability')
    for path in (
        'qorg.qorg.governance_accountability.provisioning.provision_governance_accountability',
        'qorg.qorg.governance_accountability.migration.migrate_procurement_complaints',
        'qorg.qorg.governance_accountability.acceptance.audit_deep_runtime_configuration',
        'qorg.qorg.governance_accountability.retention.run_daily_retention_jobs',
    ):
        try: frappe.get_attr(path); result['checks'][f'import:{path}']=True
        except Exception as exc: result['checks'][f'import:{path}']=False; result['errors'].append(f'{path}: {exc}')
    result['ok']=not result['errors'] and all(result['checks'].values())
    return result
