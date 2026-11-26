# Server Script: Job Requisition - Sync Role Code from Workforce Plan
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

for row in doc.custom_roles:
    if row.workforce_plan_position:
        wpp_code = frappe.db.get_value("Workforce Plan Position", row.workforce_plan_position, "role_code")
        if wpp_code and row.role_code != wpp_code:
            row.role_code = wpp_code
