# Server Script: Workforce Plan - Hide Confidential
# Type: Permission Query | DocType: Workforce Plan
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
privileged = (user == "Administrator") or ("System Manager" in roles) or ("HR Manager" in roles) or ("HOD" in roles)
if not privileged:
    conditions = "ifnull(`tabWorkforce Plan`.custom_confidential_hiring, 0) = 0"
