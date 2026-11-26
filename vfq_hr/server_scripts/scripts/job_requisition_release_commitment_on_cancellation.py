# Server Script: Job Requisition - Release Commitment on Cancellation
# Type: DocType Event | DocType: Job Requisition | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.status == "Cancelled" and doc.get("custom_budget_consumed") and doc.custom_budget_plan and not doc.get("custom_commitment_released"):
    flt = frappe.utils.flt
    positions = flt(doc.no_of_positions)
    openings = [o.name for o in frappe.get_all("Job Opening", filters={"job_requisition": doc.name}, fields=["name"])]
    onboarded = 0
    if openings:
        onboarded = len(frappe.get_all("Job Applicant", filters={"job_title": ["in", openings], "custom_recruitment_status": "Onboarded"}, fields=["name"]))
    open_positions = max(positions - onboarded, 0)
    release_budget = (flt(doc.custom_annual_budget_impact) / positions * open_positions) if positions else 0
    plan = frappe.get_doc("Workforce Plan", doc.custom_budget_plan)
    committed_hc = max(flt(plan.committed_headcount) - open_positions, 0)
    committed_budget = max(flt(plan.committed_budget) - release_budget, 0)
    open_hc = max(flt(plan.approved_headcount) - committed_hc - flt(plan.consumed_headcount), 0)
    plan.db_set("committed_headcount", committed_hc)
    plan.db_set("committed_budget", committed_budget)
    plan.db_set("remaining_headcount", flt(plan.approved_headcount) - committed_hc - flt(plan.consumed_headcount))
    plan.db_set("remaining_budget", flt(plan.total_budget_impact) - committed_budget - flt(plan.consumed_budget))
    plan.db_set("custom_positions_summary", str(int(flt(plan.consumed_headcount))) + " filled / " + str(int(open_hc)) + " open / " + str(int(flt(plan.approved_headcount))) + " approved")
    doc.db_set("custom_commitment_released", 1)
