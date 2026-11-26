# Server Script: Review Access - Relationship Lookup
# Type: API | API method: get_review_access
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

user = frappe.session.user
emp = frappe.form_dict.employee
roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
is_sys = user == "Administrator" or "System Manager" in roles
me = frappe.db.get_value("Employee", {"user_id": user}, "name")
is_self = bool(me) and bool(emp) and me == emp
boss = frappe.db.get_value("Employee", emp, "reports_to") if emp else None
is_mgr = bool(me) and bool(boss) and boss == me and not is_self
is_hr = (not is_self) and ("HR User" in roles or "HR Manager" in roles)
frappe.response["message"] = {"is_sys": is_sys, "is_self": is_self, "is_mgr": is_mgr, "is_hr": is_hr}
