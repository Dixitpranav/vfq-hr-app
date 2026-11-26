# Server Script: Employee Exit - One Open Resignation per Employee
# Type: DocType Event | DocType: Employee Exit | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

def run_script(doc):
    if not doc.is_new() or not doc.employee:
        return
    existing = frappe.get_all("Employee Exit", filters={"employee": doc.employee, "workflow_state": ["!=", "Rejected"], "docstatus": ["!=", 2]}, fields=["name", "workflow_state"], order_by="creation desc", limit_page_length=1)
    if existing:
        prev = existing[0]
        state = prev.workflow_state or "Draft"
        frappe.throw(f"A resignation ({prev.name}) already exists for this employee with status '{state}'. A new request can only be raised if the previous one is Rejected.", title="Resignation Already Raised")

run_script(doc)
