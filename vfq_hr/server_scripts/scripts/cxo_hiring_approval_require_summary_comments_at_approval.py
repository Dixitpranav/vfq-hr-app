# Server Script: CXO Hiring Approval - Require Summary Comments at Approval
# Type: DocType Event | DocType: CXO Hiring Approval | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
if before and before.workflow_state == "Draft" and doc.workflow_state in ("Pending Head of OD Approval", "Pending CAO Approval"):
    missing = []
    for r in (doc.get("standard_approvals") or []):
        if not r.hr_comments or not r.recommendation_from_project_team:
            missing.append("Standard row " + str(r.idx))
    for r in (doc.get("exceptional_approvals") or []):
        if not r.hr_comments:
            missing.append("Exceptional row " + str(r.idx))
    if missing:
        frappe.throw("Fill HR Comments and Recommendation from Project Team before sending for approval: " + ", ".join(missing), title="Summary Comments Required")
