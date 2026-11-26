# Server Script: Annual Performance Review - Set Notification Recipients
# Type: DocType Event | DocType: Annual Performance Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Keeps the employee and reporting manager email addresses used by workflow notifications up to date.
doc.custom_notify_employee_email = ""
doc.custom_notify_manager_email = ""
if doc.get("employee"):
    info = frappe.db.get_value("Employee", doc.employee, ["user_id", "company_email", "personal_email", "reports_to"], as_dict=True)
    if info:
        doc.custom_notify_employee_email = info.user_id or info.company_email or info.personal_email or ""
        if info.reports_to:
            manager = frappe.db.get_value("Employee", info.reports_to, ["user_id", "company_email", "personal_email"], as_dict=True)
            if manager:
                doc.custom_notify_manager_email = manager.user_id or manager.company_email or manager.personal_email or ""
