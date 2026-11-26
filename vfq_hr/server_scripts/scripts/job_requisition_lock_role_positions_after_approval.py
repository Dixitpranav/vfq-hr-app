# Server Script: Job Requisition - Lock Role Positions After Approval
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
if before and (before.get("workflow_state") == "Approved" or before.docstatus == 1):
    old_counts = {}
    for r in (before.get("custom_roles") or []):
        old_counts[r.name] = frappe.utils.cint(r.no_of_positions)
    for r in (doc.get("custom_roles") or []):
        if r.name in old_counts and old_counts[r.name] != frappe.utils.cint(r.no_of_positions):
            frappe.throw("Role row " + str(r.idx) + ": No. of Positions cannot be changed after the Job Requisition is approved.", title="Locked")
