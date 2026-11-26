# Server Script: Job Requisition - Restore Designation After Duplicate Check
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

roles = doc.get("custom_roles") or []
if roles and roles[0].designation:
    doc.designation = roles[0].designation
