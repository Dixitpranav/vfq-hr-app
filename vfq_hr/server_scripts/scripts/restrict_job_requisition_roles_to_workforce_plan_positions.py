# Server Script: Restrict Job Requisition Roles to Workforce Plan Positions
# Type: DocType Event | DocType: Job Requisition | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Server-side enforcement: a Job Requisition Role row's Designation must be one
# of the positions listed in the selected Workforce Plan (custom_budget_plan).
# The client-side Designation picker already filters to these positions (see
# Client Script "Budget plan to Job req auto populate fields"), but this check
# ensures the restriction holds even if a row was added before a plan was
# selected, or the plan was changed after rows already existed.

if doc.custom_budget_plan:
    workforce_plan = frappe.get_doc("Workforce Plan", doc.custom_budget_plan)
    allowed_designations = set(
        p.position for p in (workforce_plan.get("positions") or []) if p.position
    )
    for row in (doc.get("custom_roles") or []):
        if row.designation and row.designation not in allowed_designations:
            frappe.throw(
                f"{frappe.bold(row.designation)} is not one of the positions listed in "
                f"Workforce Plan {frappe.bold(doc.custom_budget_plan)}. Only positions from "
                f"the selected Workforce Plan can be added to this requisition's Roles table.",
                title="Position Not In Workforce Plan"
            )
