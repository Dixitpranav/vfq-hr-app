# Server Script: Employee Exit - Reason Chosen by Manager
# Type: DocType Event | DocType: Employee Exit | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Exit reason is chosen by the manager from the Exit Reason list, not typed by the employee.
roles = frappe.db.get_all("Has Role", filters={"parent": frappe.session.user, "parenttype": "User"}, pluck="role")
manager_roles = ["HOD", "HR Manager", "System Manager", "Reporting Manager", "Line Manager"]
can_pick = frappe.session.user == "Administrator"
for r in roles:
    if r in manager_roles:
        can_pick = True
before = doc.get_doc_before_save()
old_reason = before.get("custom_exit_reason") if before else None
old_state_r = (before.get("workflow_state") if before else None) or "Draft"
if doc.get("custom_exit_reason") != old_reason and not can_pick and old_state_r != "Draft":
    frappe.throw("After submission, only your manager or HR can change the Reason for Leaving. You can add details in Additional Comments.", title="Exit Reason Is Set by the Manager")
if doc.get("custom_exit_reason"):
    rt = frappe.db.get_value("Exit Reason", doc.custom_exit_reason, "exit_type")
    if rt and doc.exit_type and rt != doc.exit_type:
        frappe.throw("The reason " + doc.custom_exit_reason + " applies to " + rt + ", not " + doc.exit_type + ". Pick a reason that matches the exit type.", title="Reason Does Not Match Exit Type")
if (doc.get("workflow_state") or "") in ["Pending HR Approval", "Approved", "Exit Closed"] and not doc.get("custom_exit_reason"):
    frappe.throw("The manager must select the Exit Reason before this exit goes any further.", title="Exit Reason Required")
