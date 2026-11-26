# Server Script: Employee - Sync Position Title
# Type: DocType Event | DocType: Employee | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Position Title (Role Classification) is the visible field; Designation is hidden but still used by HRMS.
# Fill whichever one is empty from the other. Never overwrite a value that is already set.
if doc.custom_role_classification and not doc.designation:
    doc.designation = doc.custom_role_classification
if doc.designation and not doc.custom_role_classification:
    doc.custom_role_classification = doc.designation
