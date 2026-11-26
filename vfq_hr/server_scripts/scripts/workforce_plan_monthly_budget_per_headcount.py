# Server Script: Workforce Plan - Monthly Budget Per Headcount
# Type: DocType Event | DocType: Workforce Plan | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

doc.custom_monthly_budget_per_headcount = frappe.utils.flt(doc.approved_budget) / 12.0
