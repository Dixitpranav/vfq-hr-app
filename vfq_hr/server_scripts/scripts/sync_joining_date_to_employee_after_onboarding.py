# Server Script: Sync Joining Date to Employee After Onboarding
# Type: DocType Event | DocType: Job Applicant | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.custom_employee_created and doc.custom_employee and doc.custom_joining_date:
    current_doj = frappe.db.get_value("Employee", doc.custom_employee, "date_of_joining")
    if (not current_doj) or frappe.utils.getdate(current_doj) != frappe.utils.getdate(doc.custom_joining_date):
        frappe.db.set_value("Employee", doc.custom_employee, "date_of_joining", frappe.utils.getdate(doc.custom_joining_date))
