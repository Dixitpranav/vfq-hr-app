# Server Script: Workforce Plan - Initiator Only Editor
# Type: DocType Event | DocType: Workforce Plan | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if not doc.is_new() and frappe.session.user != doc.owner and frappe.session.user != "Administrator":
    old_state = frappe.db.get_value("Workforce Plan", doc.name, "workflow_state")
    if old_state == doc.workflow_state:
        frappe.throw(
            "Only the plan initiator (" + doc.owner + ") can edit this Workforce Plan. " +
            "If you need to make changes, please send it back for review."
        )
