# Server Script: Probation Extension - Validate
# Type: DocType Event | DocType: Probation Extension | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Months 1-6, maximum 2 extensions, active employee, revised date calculated.
months = frappe.utils.cint(doc.extension_months)
if months < 1 or months > 6:
    frappe.throw("Choose an extension period from 1 to 6 months.", title="Extension Period Required")
if not (doc.reason or "").strip():
    frappe.throw("Enter the reason for the extension.", title="Reason Required")
if frappe.db.get_value("Employee", doc.employee, "status") != "Active":
    frappe.throw("Probation can only be extended for an Active employee.", title="Employee Not Active")
used = frappe.db.count("Probation Extension", {"employee": doc.employee, "workflow_state": ["in", ["Pending HR Approval", "Approved"]], "name": ["!=", doc.name or ""]})
if used >= 2:
    frappe.throw("This employee has already used 2 probation extensions, which is the maximum.", title="Extension Limit Reached")
doc.extension_number = used + 1
doc.revised_end_date = frappe.utils.add_months(frappe.utils.getdate(doc.current_end_date), months)
