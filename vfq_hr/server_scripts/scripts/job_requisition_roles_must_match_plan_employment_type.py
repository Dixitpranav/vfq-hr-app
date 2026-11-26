# Server Script: Job Requisition - Roles Must Match Plan Employment Type
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Each role's employment type must be the one set on its Workforce Plan position.
for r in (doc.get("custom_roles") or []):
    pos = r.get("workforce_plan_position")
    if not pos:
        continue
    plan_type = frappe.db.get_value("Workforce Plan Position", pos, "custom_employment_type")
    role_type = r.get("custom_employment_type")
    if plan_type and not role_type:
        r.custom_employment_type = plan_type
    elif plan_type and role_type and plan_type != role_type:
        frappe.throw("Role " + (r.role_title or r.designation or "") + " has employment type " + role_type + ", but the Workforce Plan position is " + plan_type + ". Employment type starts in the plan and cannot be changed here.", title="Employment Type Mismatch")
