# Server Script: Employee Exit - Portal Resignation Defaults
# Type: API | API method: get_my_resignation_defaults
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

user = frappe.session.user
cint = frappe.utils.cint
emp = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, ["name", "employee_name", "notice_number_of_days", "custom_vendor"], as_dict=True)
days = 0
emp_name = None
emp_label = None
if emp:
    emp_name = emp.name
    emp_label = emp.employee_name
    days = cint(emp.notice_number_of_days)
    if not days and emp.custom_vendor:
        days = cint(frappe.db.get_value("Supplier", emp.custom_vendor, "custom_notice_period_days"))
reasons = frappe.get_all("Exit Reason", filters={"enabled": 1, "exit_type": ["in", ["Resignation", "Retirement", "End of Contract"]]}, fields=["name", "exit_type"], order_by="name asc")
open_exit = None
if emp_name:
    found = frappe.get_all("Employee Exit", filters={"employee": emp_name, "workflow_state": ["!=", "Rejected"], "docstatus": ["!=", 2]}, fields=["name", "workflow_state"], order_by="creation desc", limit_page_length=1)
    if found:
        open_exit = found[0]
frappe.response["message"] = {"open_exit": open_exit, "employee": emp_name, "employee_name": emp_label, "notice_days": days, "today": frappe.utils.nowdate(), "reasons": reasons}
