# Server Script: Update Employee Confirmation Status (On Submit)
# Type: DocType Event | DocType: Probation Review | Event: After Submit
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

mapping = {
    "Confirm": "Confirmed",
    "Extend Probation": "Extended",
    "Terminate": "Terminated"
}
new_status = mapping.get(doc.decision)
if new_status and doc.employee:
    employee = frappe.get_doc("Employee", doc.employee)
    if employee.get("custom_confirmation_status") != new_status:
        employee.db_set("custom_confirmation_status", new_status)
