# Server Script: CXO Hiring Approval - Save Send Back Reason
# Type: API | API method: save_cxo_send_back_reason
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

batch = frappe.form_dict.get("batch")
reason = (frappe.form_dict.get("reason") or "").strip()
if not batch or not frappe.db.exists("CXO Hiring Approval", batch):
    frappe.throw("CXO Hiring Approval not found.")
state = frappe.db.get_value("CXO Hiring Approval", batch, "workflow_state")
role = None
if state == "Pending Head of OD Approval":
    role = "Head of OD & Total Rewards"
elif state == "Pending CHRO Approval":
    role = "CHRO"
elif state == "Pending CAO Approval":
    role = "CAO"
elif state == "Pending CEO Approval":
    role = "CEO / Final Approver"
if not role:
    frappe.throw("This batch can only be sent back while it is waiting for an approver (Head of OD, CHRO, CAO or CEO).")
if not frappe.db.exists("Has Role", {"parent": frappe.session.user, "parenttype": "User", "role": role}):
    frappe.throw("Only the " + role + " can send this batch back at this stage.", frappe.PermissionError)
if len(reason) < 10:
    frappe.throw("Enter a clear reason of at least 10 characters.")
frappe.db.set_value("CXO Hiring Approval", batch, "custom_send_back_reason", reason, update_modified=False)
frappe.response["message"] = "ok"
