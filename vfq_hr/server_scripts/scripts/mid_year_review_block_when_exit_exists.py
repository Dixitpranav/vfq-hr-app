# Server Script: Mid-Year Review - Block When Exit Exists
# Type: DocType Event | DocType: Mid-Year Review | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# A review cannot be created, saved, submitted or moved to another workflow stage while the employee has a
# resignation / exit record that is not Rejected (or cancelled). System-driven saves (ignore_permissions) are not blocked.
def run_script(doc):
    if doc.flags.ignore_permissions or not doc.employee:
        return
    ex = frappe.get_all("Employee Exit", filters={"employee": doc.employee, "workflow_state": ["!=", "Rejected"], "docstatus": ["!=", 2]}, fields=["name", "workflow_state"], order_by="creation desc", limit_page_length=1)
    if not ex:
        return
    who = doc.get("employee_name") or doc.employee
    frappe.throw(
        f"This {doc.doctype} cannot proceed: {who} has a resignation / exit record {ex[0].name} (status: {ex[0].workflow_state or 'Draft'}). Reviews can continue only after that record is Rejected or cancelled.",
        title="Employee Has an Exit Record",
    )

run_script(doc)
