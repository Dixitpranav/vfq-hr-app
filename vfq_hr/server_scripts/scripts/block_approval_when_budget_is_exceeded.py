# Server Script: Block Approval When Budget Is Exceeded
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

allow_overconsumption = frappe.db.get_single_value("HR Settings", "custom_allow_budget_overconsumption")

if doc.workflow_state == "Approved":

    annual_impact = doc.custom_annual_budget_impact or 0
    requested_positions = doc.no_of_positions or 0

    remaining_budget = 0
    remaining_headcount = 0
    if doc.custom_budget_plan:
        budget_plan = frappe.get_doc("Workforce Plan", doc.custom_budget_plan)
        remaining_budget = (
            frappe.utils.flt(budget_plan.total_budget_impact)
            - frappe.utils.flt(budget_plan.committed_budget)
            - frappe.utils.flt(budget_plan.consumed_budget)
        )
        remaining_headcount = (
            frappe.utils.flt(budget_plan.approved_headcount)
            - frappe.utils.flt(budget_plan.committed_headcount)
            - frappe.utils.flt(budget_plan.consumed_headcount)
        )

    doc.custom_budget_variance_usd = max(annual_impact - remaining_budget, 0)
    doc.custom_headcount_variance = max(requested_positions - remaining_headcount, 0)

    if not allow_overconsumption:
        if annual_impact > remaining_budget:
            frappe.throw(
                f"Budget exceeded. Required: {annual_impact}, Available: {remaining_budget}"
            )

        if requested_positions > remaining_headcount:
            frappe.throw(
                f"Headcount exceeded. Requested: {requested_positions}, Available: {remaining_headcount}"
            )
