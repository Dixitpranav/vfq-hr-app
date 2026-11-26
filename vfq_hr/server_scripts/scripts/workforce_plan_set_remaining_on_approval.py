# Server Script: Workforce Plan - Set Remaining On Approval
# Type: DocType Event | DocType: Workforce Plan | Event: After Submit
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

doc.db_set("remaining_budget", frappe.utils.flt(doc.total_budget_impact) - frappe.utils.flt(doc.committed_budget) - frappe.utils.flt(doc.consumed_budget))
doc.db_set("remaining_headcount", frappe.utils.flt(doc.approved_headcount) - frappe.utils.flt(doc.committed_headcount) - frappe.utils.flt(doc.consumed_headcount))
