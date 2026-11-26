# Server Script: Probation Extension - Apply Decision
# Type: DocType Event | DocType: Probation Extension | Event: After Save
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

if doc.get("new_probation_review") or doc.workflow_state not in ["Approved", "Rejected"]:
    pass
else:
    emp = frappe.get_doc("Employee", doc.employee)
    review = frappe.get_doc("Probation Review", doc.probation_review)
    approved = doc.workflow_state == "Approved"
    new_end = doc.revised_end_date if approved else doc.current_end_date
    if approved:
        if not emp.get("custom_original_probation_end_date"):
            emp.db_set("custom_original_probation_end_date", doc.current_end_date)
        emp.db_set("custom_probation_end_date", new_end)
        emp.db_set("custom_probation_months", frappe.utils.cint(emp.get("custom_probation_months")) + frappe.utils.cint(doc.extension_months))
        emp.db_set("custom_probation_extension_count", frappe.utils.cint(emp.get("custom_probation_extension_count")) + 1)
        emp.db_set("custom_confirmation_status", "Extended")
    else:
        emp.db_set("custom_confirmation_status", "Probation")
    nr = frappe.get_doc({"doctype": "Probation Review", "employee": emp.name, "employee_name": emp.employee_name, "department": emp.department, "designation": emp.designation, "reviewer": doc.manager or emp.reports_to, "date_of_joining": emp.date_of_joining, "probation_end_date": new_end, "custom_previous_review": review.name, "auto_created": 1})
    nr.insert(ignore_permissions=True)
    doc.db_set("new_probation_review", nr.name)
    if approved:
        subject = "Probation extended for " + emp.employee_name
        body = "Probation for " + emp.employee_name + " is extended by " + str(doc.extension_months) + " month(s). Revised end date: " + str(new_end) + ". A new Probation Review " + nr.name + " has been created."
    else:
        subject = "Probation extension rejected for " + emp.employee_name
        body = "The extension request " + doc.name + " was rejected by HR. HR remarks: " + (doc.hr_remarks or "none") + ". A new Probation Review " + nr.name + " has been created for the existing end date " + str(new_end) + " so a fresh decision can be taken."
    notify([emp_user(emp.name), emp_user(doc.manager or emp.reports_to)] + hr_users(), subject, "Probation Review", nr.name, body)
