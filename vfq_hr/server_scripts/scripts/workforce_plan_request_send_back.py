# Server Script: Workforce Plan - Request Send Back
# Type: API | API method: request_workforce_plan_send_back
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

plan = frappe.form_dict.get("plan")
reason = (frappe.form_dict.get("reason") or "").strip()
if not plan or not frappe.db.exists("Workforce Plan", plan):
    frappe.throw("Workforce Plan not found.")
doc = frappe.get_doc("Workforce Plan", plan)
if frappe.session.user != doc.owner:
    frappe.throw("Only the creator of this Workforce Plan can request it back for review.", frappe.PermissionError)
state = doc.workflow_state or ""
if doc.docstatus != 0 or not state.startswith("Pending "):
    frappe.throw("A send back can only be requested while the plan is in approval.")
if doc.get("custom_send_back_requested"):
    frappe.throw("A send back request is already waiting with the approver.")
if len(reason) < 10:
    frappe.throw("Enter a clear reason of at least 10 characters.")
requested_by = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
frappe.db.set_value("Workforce Plan", plan, {
    "custom_send_back_requested": 1,
    "custom_send_back_reason": reason,
    "custom_send_back_requested_by": requested_by,
    "custom_send_back_requested_on": frappe.utils.now()
}, update_modified=False)
safe_reason = reason.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
doc.add_comment("Comment", "Send back for review requested at " + state + ". Reason: " + safe_reason)
roles = []
for t in frappe.get_all("Workflow Transition", filters={"parent": "Workforce Plan Approval", "state": state, "action": "Approve"}, fields=["allowed"]):
    roles.append(t.allowed)
role_users = []
for r in frappe.get_all("Has Role", filters={"role": ["in", roles], "parenttype": "User"}, fields=["parent"]):
    role_users.append(r.parent)
recipients = []
for u in frappe.get_all("User", filters={"name": ["in", role_users or [""]], "enabled": 1}, fields=["name"]):
    if u.name not in ("Administrator", "Guest", doc.owner) and u.name not in recipients:
        recipients.append(u.name)
for user in recipients:
    frappe.get_doc({
        "doctype": "Notification Log",
        "for_user": user,
        "from_user": frappe.session.user,
        "type": "Alert",
        "document_type": "Workforce Plan",
        "document_name": plan,
        "subject": requested_by + " requested Workforce Plan " + plan + " back for review"
    }).insert(ignore_permissions=True)
frappe.response["message"] = len(recipients)
