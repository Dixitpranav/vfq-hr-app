# Server Script: Sync Designation From First Role (Before Validate)
# Type: DocType Event | DocType: Job Requisition | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# The standard HRMS check blocks a second requisition with the same requester, department and designation.
# The same role can legitimately be raised again (for example with a different vendor), so the hidden legacy
# designation holds a neutral value during that check. "Job Requisition - Restore Designation After Duplicate Check"
# puts the first role's designation back straight afterwards.
roles = doc.get("custom_roles") or []
if roles and roles[0].designation:
    doc.designation = "__repeat_role_allowed__"
