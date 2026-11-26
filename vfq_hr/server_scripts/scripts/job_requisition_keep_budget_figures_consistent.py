# Server Script: Job Requisition - Keep Budget Figures Consistent
# Type: DocType Event | DocType: Job Requisition | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Keeps the requisition's own budget figures correct whatever way it was created (form, import or API).
# Approved = what this requisition asks for. Remaining = Approved - Consumed. 0 when fully used, negative when over-used.
total_hc = 0
total_cost = 0
for r in (doc.get("custom_roles") or []):
    total_hc = total_hc + frappe.utils.flt(r.no_of_positions)
    total_cost = total_cost + frappe.utils.flt(r.total_estimated_cost_usd)
approved_budget = frappe.utils.flt(doc.get("custom_annual_budget_impact")) or total_cost
approved_hc = total_hc or frappe.utils.flt(doc.get("no_of_positions"))
consumed_budget = frappe.utils.flt(doc.get("custom_consumed_budget"))
consumed_hc = frappe.utils.flt(doc.get("custom_consumed_headcount"))
doc.db_set("custom_approved_budget", approved_budget)
doc.db_set("custom_approved_headcount", approved_hc)
doc.db_set("custom_remaining_budget", approved_budget - consumed_budget)
doc.db_set("custom_remaining_headcount", approved_hc - consumed_hc)
