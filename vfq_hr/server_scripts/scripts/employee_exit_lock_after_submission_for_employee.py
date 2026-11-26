# Server Script: Employee Exit - Lock After Submission for Employee
# Type: DocType Event | DocType: Employee Exit | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

def run_script(doc):
    if doc.is_new():
        return
    before = doc.get_doc_before_save()
    if not before:
        return
    old_state = before.workflow_state or "Draft"
    if old_state == "Draft":
        return
    if (doc.workflow_state or "Draft") != old_state:
        return
    user = frappe.session.user
    if user == "Administrator":
        return
    emp_user = frappe.db.get_value("Employee", doc.employee, "user_id") if doc.employee else None
    if not emp_user or emp_user != user:
        return
    hr_roles = ["HR Manager", "HR User", "System Manager"]
    if frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": ["in", hr_roles]}):
        return
    frappe.throw(f"Your resignation is now '{old_state}' and can no longer be changed. Please contact HR if something needs correcting.", title="Resignation Locked")

run_script(doc)
