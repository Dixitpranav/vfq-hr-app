# Server Script: Compute Job Opening Closing SLA Days
# Type: DocType Event | DocType: Job Opening | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.closes_on:
    doc.custom_closing_sla_days = frappe.utils.date_diff(doc.closes_on, frappe.utils.today())
else:
    doc.custom_closing_sla_days = None
