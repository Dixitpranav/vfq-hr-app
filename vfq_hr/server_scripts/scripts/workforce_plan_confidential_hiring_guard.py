# Server Script: Workforce Plan - Confidential Hiring Guard
# Type: DocType Event | DocType: Workforce Plan | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
old_val = 0
if before:
    old_val = frappe.utils.cint(before.get("custom_confidential_hiring"))
new_val = frappe.utils.cint(doc.get("custom_confidential_hiring"))
skip = False

if old_val != new_val and not skip:
    user_roles = frappe.db.get_all("Has Role", filters={"parent": frappe.session.user, "parenttype": "User"}, pluck="role")
    allowed = False
    for role_name in ["HR Manager", "HOD", "System Manager"]:
        if role_name in user_roles:
            allowed = True
    if frappe.session.user == "Administrator":
        allowed = True
    if not allowed:
        frappe.throw("Only an HR Manager or an HOD can change Confidential Hiring on this document.", title="Confidential Hiring")
