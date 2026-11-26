# Server Script: Probation Review - Extension Validation
# Type: DocType Event | DocType: Probation Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# When the decision is Extend Probation: months, reason, active employee, and a maximum of 2 extensions.
if doc.decision == "Extend Probation":
    months = frappe.utils.cint(doc.get("custom_extension_months"))
    if months < 1 or months > 6:
        frappe.throw("Choose the extension period, from 1 to 6 months.", title="Extension Period Required")
    if not (doc.get("custom_extension_reason") or "").strip():
        frappe.throw("Enter the reason for extending the probation.", title="Reason Required")
    if frappe.db.get_value("Employee", doc.employee, "status") != "Active":
        frappe.throw("Probation can only be extended for an Active employee.", title="Employee Not Active")
    used = frappe.db.count("Probation Extension", {"employee": doc.employee, "workflow_state": ["in", ["Pending HR Approval", "Approved"]], "probation_review": ["!=", doc.name or ""]})
    if used >= 2:
        frappe.throw("This employee has already used 2 probation extensions, which is the maximum. Choose Confirm or Terminate.", title="Extension Limit Reached")
    if doc.probation_end_date:
        doc.custom_revised_end_date = frappe.utils.add_months(frappe.utils.getdate(doc.probation_end_date), months)
    doc.custom_extension_number = used + 1
else:
    doc.custom_revised_end_date = None
