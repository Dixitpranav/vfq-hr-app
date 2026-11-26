# Server Script: Workforce Plan - Sync Position Title
# Type: DocType Event | DocType: Workforce Plan | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Position Title (Role Classification) is the visible field; Designation is hidden but still used by HRMS.
# Fill whichever one is empty from the other. Never overwrite a value that is already set.
for r in (doc.get("positions") or []):
    if r.role_classification and not r.position:
        r.position = r.role_classification
    if r.position and not r.role_classification:
        r.role_classification = r.position
