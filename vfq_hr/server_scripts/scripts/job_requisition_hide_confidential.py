# Server Script: Job Requisition - Hide Confidential
# Type: Permission Query | DocType: Job Requisition
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
privileged = (user == "Administrator") or ("System Manager" in roles) or ("HR Manager" in roles) or ("HOD" in roles)
if not privileged:
    conditions = "ifnull(`tabJob Requisition`.custom_confidential_hiring, 0) = 0"
