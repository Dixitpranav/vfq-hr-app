# Server Script: Employee - Grant Self Service Permissions
# Type: DocType Event | DocType: Employee | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Wrapped in one function so the helper functions can call each other
# (Server Script sandbox cannot see top-level functions from inside another function).
def run_script(doc):
    # Grants each self-service user a User Permission on their own Employee (and, for managers, on each team member)
    # for the self-service doctypes only. It only ADDS what is missing; it never removes anything.
    SS_DOCTYPES = ["Employee", "Employee Exit", "Leave Application", "Leave Allocation", "Attendance", "Attendance Request", "Probation Review", "Probation Extension", "Mid-Year Review", "Annual Performance Review", "Salary Slip", "Expense Claim", "Employee Advance"]
    HR_ROLES = ["HR Manager", "HR User", "System Manager"]
    MGR_ROLES = ["HOD", "Reporting Manager", "Line Manager", "Leave Approver", "Expense Approver"]
    # Approvers and business roles pick other employees on plans and requisitions, so the Employee master stays open to them (sensitive fields are level 1).
    BUSINESS_ROLES = ["HOD", "CAO", "CEO / Final Approver", "CHRO", "Functional Head", "Head of OD & Total Rewards", "Recruitment Specialist", "Vendor Manager"]

    def roles_of(user):
        return frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")

    def descendants(emp):
        found = []
        level = [emp]
        depth = 0
        while level and depth < 8:
            reports = frappe.db.get_all("Employee", filters={"reports_to": ["in", level], "status": "Active"}, pluck="name")
            new = []
            for r in reports:
                if r not in found and r != emp:
                    found.append(r)
                    new.append(r)
            level = new
            depth = depth + 1
        return found

    def sync_user(user, emp_name):
        roles = roles_of(user)
        is_hr = False
        is_mgr = False
        for r in roles:
            if r in HR_ROLES:
                is_hr = True
            if r in MGR_ROLES:
                is_mgr = True
        if is_hr:
            return "HR role, left unrestricted"
        is_business = False
        for r in roles:
            if r in BUSINESS_ROLES:
                is_business = True
        doctypes = [d for d in SS_DOCTYPES if not (is_business and d == "Employee")]
        allowed = [emp_name]
        if is_mgr:
            for d in descendants(emp_name):
                allowed.append(d)
        existing = frappe.db.get_all("User Permission", filters={"user": user, "allow": "Employee"}, fields=["for_value", "applicable_for", "apply_to_all_doctypes"])
        have = {}
        for ex in existing:
            if ex.apply_to_all_doctypes:
                for dt in SS_DOCTYPES:
                    have[ex.for_value + "|" + dt] = 1
            elif ex.applicable_for:
                have[ex.for_value + "|" + ex.applicable_for] = 1
        added = 0
        for e in allowed:
            for dt in doctypes:
                if (e + "|" + dt) not in have:
                    frappe.get_doc({"doctype": "User Permission", "user": user, "allow": "Employee", "for_value": e, "apply_to_all_doctypes": 0, "applicable_for": dt, "is_default": 0}).insert(ignore_permissions=True)
                    added = added + 1
        return ("manager" if is_mgr else "employee") + ", may see " + str(len(allowed)) + " employee(s); added " + str(added) + " permission rows"

    def sync_all():
        lines = []
        for e in frappe.db.get_all("Employee", filters={"status": "Active", "user_id": ["is", "set"]}, fields=["name", "user_id"]):
            if e.user_id in ["Administrator", "Guest"]:
                continue
            lines.append(e.user_id + " (" + e.name + "): " + sync_user(e.user_id, e.name))
        return lines

    try:
        sync_all()
    except Exception:
        frappe.log_error(title="Self service permission sync failed on " + doc.name)


run_script(doc)
