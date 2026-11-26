# Server Script: Job Requisition - Sync Position Title
# Type: DocType Event | DocType: Job Requisition | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Position Title (Role Classification) is the visible field; Designation is hidden but still used by HRMS.
# Fill whichever one is empty from the other. Never overwrite a value that is already set.
for r in (doc.get("custom_roles") or []):
    if r.role_classification and not r.designation:
        r.designation = r.role_classification
    if r.designation and not r.role_classification:
        r.role_classification = r.designation
