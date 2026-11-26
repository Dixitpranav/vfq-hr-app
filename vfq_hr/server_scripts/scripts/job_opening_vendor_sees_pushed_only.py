# Server Script: Job Opening - Vendor Sees Pushed Only
# Type: Permission Query | DocType: Job Opening
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
privileged = (user == "Administrator") or ("System Manager" in roles) or ("HR Manager" in roles) or ("HOD" in roles)
clauses = []
if not privileged:
    clauses.append("ifnull(`tabJob Opening`.custom_confidential_hiring, 0) = 0")
if ("Job Opening Vendor" in roles) and not ("HR User" in roles) and not privileged:
    clauses.append("`tabJob Opening`.custom_pushed_to_vendor = 1")
if clauses:
    conditions = " and ".join(clauses)
