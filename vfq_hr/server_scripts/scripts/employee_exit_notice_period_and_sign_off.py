# Server Script: Employee Exit - Notice Period and Sign-off
# Type: DocType Event | DocType: Employee Exit | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

cint = frappe.utils.cint
user = frappe.session.user
hr_roles = ["HR Manager", "HR User", "System Manager"]
is_hr = user == "Administrator" or bool(frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": ["in", hr_roles]}))
before = doc.get_doc_before_save()
old_state = before.workflow_state if before else None
new_state = doc.workflow_state

# 1. Notice period comes from the employee record. Only HR can change it (or the Last Working Day).
if not doc.notice_date:
    doc.notice_date = frappe.utils.nowdate()
emp_notice = cint(frappe.db.get_value("Employee", doc.employee, "notice_number_of_days")) if doc.employee else 0
if doc.employee and not emp_notice:
    emp_vendor = frappe.db.get_value("Employee", doc.employee, "custom_vendor")
    if emp_vendor:
        emp_notice = cint(frappe.db.get_value("Supplier", emp_vendor, "custom_notice_period_days"))
if not is_hr:
    doc.custom_notice_period_days = emp_notice
elif not cint(doc.custom_notice_period_days):
    doc.custom_notice_period_days = emp_notice
days = cint(doc.custom_notice_period_days)
if doc.notice_date and days:
    expected = frappe.utils.add_days(doc.notice_date, days)
    notice_changed = before and (cint(before.get("custom_notice_period_days")) != days or str(before.get("notice_date") or "") != str(doc.notice_date))
    lwd_changed_by_hr = is_hr and before and str(before.get("last_working_day") or "") != str(doc.last_working_day or "")
    if not is_hr or not doc.last_working_day or (notice_changed and not lwd_changed_by_hr):
        doc.last_working_day = expected

# 2. Reason for leaving is required when the employee submits a resignation.
if new_state == "Pending Manager Approval" and old_state != new_state and doc.exit_type == "Resignation" and not doc.get("custom_exit_reason"):
    frappe.throw("Please choose a Reason for Leaving before you submit your resignation.", title="Reason for Leaving required")

# 3. Digital sign-off: name, employee ID and time of each step.
if old_state != new_state:
    now = frappe.utils.now_datetime()
    full_name = frappe.db.get_value("User", user, "full_name") or user
    user_emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
    signer = full_name + (" (" + user_emp + ")" if user_emp else " (" + user + ")")
    if new_state == "Pending Manager Approval" and not doc.get("custom_employee_signed_by"):
        emp_sig = (doc.employee_name or full_name) + " (" + (doc.employee or "") + ")"
        if user_emp and user_emp != doc.employee:
            emp_sig = emp_sig + ", submitted by " + signer
        doc.custom_employee_signed_by = emp_sig
        doc.custom_employee_signed_on = now
    if old_state == "Pending Manager Approval" and new_state == "Pending HR Approval":
        doc.custom_manager_signed_by = signer
        doc.custom_manager_signed_on = now
    if old_state == "Pending HR Approval" and new_state == "Approved":
        doc.custom_hr_signed_by = signer
        doc.custom_hr_signed_on = now
