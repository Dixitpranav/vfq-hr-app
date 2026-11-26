# Server Script: Leave Application Status Bypass for the workflow
# Type: DocType Event | DocType: Leave Application | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.workflow_state == "Approved":
    doc.status = "Approved"

elif doc.workflow_state == "Rejected":
    doc.status = "Rejected"

else:
    doc.status = "Open"
