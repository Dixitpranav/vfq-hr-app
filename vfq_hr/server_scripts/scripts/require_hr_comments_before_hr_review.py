# Server Script: Require HR Comments Before HR Review
# Type: DocType Event | DocType: Probation Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.workflow_state == "Final Decision" and not doc.get("hr_feedback"):
    frappe.throw("HR Comments is required before finalizing the Probation Review.")
