# Server Script: Compute Workforce Plan Summary Fields
# Type: DocType Event | DocType: Workforce Plan | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Computes the Workforce Plan summary fields (utilization % and a human-readable
# positions summary) from the existing approved/committed/consumed/remaining
# headcount and budget fields. Purely additive -- does not change how those
# underlying fields are calculated elsewhere.
approved_hc = frappe.utils.flt(doc.approved_headcount)
committed_hc = frappe.utils.flt(doc.committed_headcount)
consumed_hc = frappe.utils.flt(doc.consumed_headcount)
budget_per_head = frappe.utils.flt(doc.approved_budget)
committed_budget = frappe.utils.flt(doc.committed_budget)
consumed_budget = frappe.utils.flt(doc.consumed_budget)

doc.total_budget_impact = approved_hc * budget_per_head
approved_budget = doc.total_budget_impact

if approved_hc > 0:
    doc.custom_headcount_utilization_pct = ((committed_hc + consumed_hc) / approved_hc) * 100
else:
    doc.custom_headcount_utilization_pct = 0

if approved_budget > 0:
    doc.custom_budget_utilization_pct = ((committed_budget + consumed_budget) / approved_budget) * 100
else:
    doc.custom_budget_utilization_pct = 0

open_hc = max(approved_hc - committed_hc - consumed_hc, 0)
doc.custom_positions_summary = str(int(consumed_hc)) + " filled / " + str(int(open_hc)) + " open / " + str(int(approved_hc)) + " approved"
