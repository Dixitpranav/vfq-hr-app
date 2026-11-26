# Server Script: Employee - Auto Reporting Manager Role
# Type: DocType Event | DocType: Employee | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Gives the "Reporting Manager" role to anyone set as an active employee's Reports To, so the
# Manager Self Service portal appears for them. The role is removed again only if it was added
# automatically and the manager no longer has any active reportees. Manually assigned roles are never touched.
role = "Reporting Manager"
before = doc.get_doc_before_save()
old_mgr = before.reports_to if before else None
old_active = (before.status == "Active") if before else False
new_mgr = doc.reports_to if doc.status == "Active" else None

if new_mgr:
    mu = frappe.db.get_value("Employee", new_mgr, "user_id")
    if mu and frappe.db.get_value("User", mu, "enabled") and not frappe.db.exists("Has Role", {"parent": mu, "parenttype": "User", "role": role}):
        usr = frappe.get_doc("User", mu)
        usr.append("roles", {"role": role})
        usr.custom_auto_reporting_manager = 1
        usr.save(ignore_permissions=True)

candidates = []
if old_mgr and old_active and old_mgr != new_mgr:
    candidates.append(old_mgr)
for c in candidates:
    left = frappe.db.count("Employee", {"reports_to": c, "status": "Active", "name": ["!=", doc.name]})
    if left == 0:
        cu = frappe.db.get_value("Employee", c, "user_id")
        if cu and frappe.db.get_value("User", cu, "custom_auto_reporting_manager"):
            usr = frappe.get_doc("User", cu)
            keep = []
            for r in usr.roles:
                if r.role != role:
                    keep.append({"role": r.role})
            usr.set("roles", keep)
            usr.custom_auto_reporting_manager = 0
            usr.save(ignore_permissions=True)
