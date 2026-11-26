# Server Script: Consume budget Automatically after final approval on job requisition
# Type: DocType Event | DocType: Job Requisition | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if (
    doc.workflow_state == "Approved"
    and doc.custom_budget_plan
    and not doc.get("custom_budget_consumed")
):
    budget_plan = frappe.get_doc("Workforce Plan", doc.custom_budget_plan)

    if budget_plan.docstatus != 1:
        frappe.throw(
            f"Job Requisition {doc.name} cannot move to \"Approved\" against Workforce Plan "
            f"{budget_plan.name}, because that plan has not been submitted/approved yet "
            f"(currently \"{budget_plan.workflow_state or 'Draft'}\"). Take the Workforce Plan through its "
            f"own approval workflow (Draft -> ... -> Approved) before approving requisitions against it.",
            title="Workforce Plan Not Approved"
        )

    new_committed_headcount = frappe.utils.flt(budget_plan.committed_headcount) + frappe.utils.flt(doc.no_of_positions)
    new_committed_budget = frappe.utils.flt(budget_plan.committed_budget) + frappe.utils.flt(doc.custom_annual_budget_impact)

    budget_plan.db_set("committed_headcount", new_committed_headcount)
    budget_plan.db_set("committed_budget", new_committed_budget)
    budget_plan.db_set(
        "remaining_headcount",
        frappe.utils.flt(budget_plan.approved_headcount)
        - new_committed_headcount
        - frappe.utils.flt(budget_plan.consumed_headcount),
    )
    budget_plan.db_set(
        "remaining_budget",
        frappe.utils.flt(budget_plan.total_budget_impact)
        - new_committed_budget
        - frappe.utils.flt(budget_plan.consumed_budget),
    )

    doc.db_set("custom_budget_consumed", 1)
