# Server Script: Annual Performance Review - Required Fields by Stage
# Type: DocType Event | DocType: Annual Performance Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
if before and before.workflow_state != doc.workflow_state and doc.workflow_state == "Employee Discussion":
    missing = []
    for r in (doc.get("kra_evaluation") or []):
        if not r.manager_comments:
            missing.append("KRA row " + str(r.idx))
    if missing:
        frappe.throw("Add Manager Comments before moving to Employee Discussion: " + ", ".join(missing), title="Required Fields")
