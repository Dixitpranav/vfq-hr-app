# Server Script: Probation Review - Raise Extension on Final Decision
# Type: DocType Event | DocType: Probation Review | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

def notify(users, subject, dt, name, body):
    sent = {}
    for u in users:
        if u and u != "Administrator" and u not in sent and frappe.db.exists("User", u):
            sent[u] = 1
            try:
                frappe.get_doc({"doctype": "Notification Log", "subject": subject, "for_user": u, "type": "Alert", "document_type": dt, "document_name": name, "email_content": body}).insert(ignore_permissions=True)
            except Exception:
                pass
    if sent:
        try:
            frappe.sendmail(recipients=list(sent.keys()), subject=subject, message=body)
        except Exception:
            pass

def hr_users():
    return frappe.db.get_all("Has Role", filters={"role": "HR Manager", "parenttype": "User"}, pluck="parent")

def emp_user(emp):
    if not emp:
        return None
    return frappe.db.get_value("Employee", emp, "user_id")

if doc.decision == "Extend Probation" and doc.docstatus == 1 and not doc.get("custom_probation_extension"):
    if not frappe.db.exists("Probation Extension", {"probation_review": doc.name}):
        ext = frappe.get_doc({"doctype": "Probation Extension", "employee": doc.employee, "probation_review": doc.name, "manager": doc.get("reviewer"), "current_end_date": doc.probation_end_date, "extension_months": str(frappe.utils.cint(doc.custom_extension_months)), "reason": doc.custom_extension_reason})
        ext.insert(ignore_permissions=True)
        doc.db_set("custom_probation_extension", ext.name)
        body = "Probation extension " + ext.name + " for " + (doc.employee_name or doc.employee) + ": " + str(ext.extension_months) + " month(s), revised end date " + str(ext.revised_end_date) + ". Reason: " + (doc.custom_extension_reason or "") + ". Please approve or reject."
        notify(hr_users(), "Probation extension needs HR approval: " + (doc.employee_name or doc.employee), "Probation Extension", ext.name, body)
