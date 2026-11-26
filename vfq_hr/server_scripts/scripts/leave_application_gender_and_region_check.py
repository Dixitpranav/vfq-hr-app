# Server Script: Leave Application - Gender and Region Check
# Type: DocType Event | DocType: Leave Application | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Gender-specific leave types can only be used by the matching gender.
ag = frappe.db.get_value("Leave Type", doc.leave_type, "custom_applicable_gender")
if ag and ag != "Any":
    g = frappe.db.get_value("Employee", doc.employee, "gender")
    if g != ag:
        frappe.throw("The leave type " + doc.leave_type + " is only for " + ag + " employees.", title="Leave Type Not Applicable")
