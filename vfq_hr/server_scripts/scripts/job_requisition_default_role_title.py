# Server Script: Job Requisition - Default Role Title
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Role / Position Title defaults to the designation so it is never blank (it becomes the Job Opening title).
for role_row in (doc.get("custom_roles") or []):
    if not role_row.role_title and role_row.designation:
        role_row.role_title = role_row.designation
