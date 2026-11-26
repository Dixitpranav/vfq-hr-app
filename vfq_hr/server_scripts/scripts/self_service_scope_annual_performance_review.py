# Server Script: Self Service Scope - Annual Performance Review
# Type: Permission Query | DocType: Annual Performance Review
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Self-service scoping for Annual Performance Review: employee sees own records, manager sees own plus team, HR sees all.
roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
open_roles = ["HR Manager", "HR User", "System Manager", "Administrator"]
is_open = user == "Administrator"
for r in roles:
    if r in open_roles:
        is_open = True
if not is_open:
    me = frappe.db.get_value("Employee", {"user_id": user}, "name")
    allowed = []
    if me:
        allowed.append(me)
    manager_roles = ["HOD", "Reporting Manager", "Line Manager", "Leave Approver", "Expense Approver"]
    is_manager = False
    for r in roles:
        if r in manager_roles:
            is_manager = True
    if is_manager and me and True:
        level = [me]
        depth = 0
        while level and depth < 6:
            reports = frappe.db.get_all("Employee", filters={"reports_to": ["in", level]}, pluck="name")
            new = []
            for e in reports:
                if e not in allowed:
                    allowed.append(e)
                    new.append(e)
            level = new
            depth = depth + 1
    if not allowed:
        allowed = ["__none__"]
    quoted = ", ".join([frappe.db.escape(a) for a in allowed])
    parts = ["`tabAnnual Performance Review`.`employee` in (" + quoted + ")"]
    if me:
        parts.append("`tabAnnual Performance Review`.`reporting_manager` = " + frappe.db.escape(me))
    conditions = "(" + " or ".join(parts) + ")"
