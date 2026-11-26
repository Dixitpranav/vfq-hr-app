# Server Script: Employee - Auto Assign Leave Policy
# Type: DocType Event | DocType: Employee | Event: After Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Wrapped in one function so the helper functions can call each other
# (Server Script sandbox cannot see top-level functions from inside another function).
def run_script(doc):
    def find_policy(emp):
        vendor = emp.get("custom_vendor")
        vendor_country = frappe.db.get_value("Supplier", vendor, "country") if vendor else None
        work_country = emp.get("custom_work_country") or frappe.db.get_value("Company", emp.company, "country")
        best = None
        best_key = -100000
        for m in frappe.db.get_all("Leave Policy Mapping", filters={"enabled": 1}, fields=["name", "leave_policy", "priority", "vendor", "vendor_country", "company", "work_country", "gender", "employment_type"]):
            score = 0
            ok = True
            if m.vendor:
                ok = ok and m.vendor == vendor
                score = score + 1
            if m.vendor_country:
                ok = ok and m.vendor_country == vendor_country
                score = score + 1
            if m.company:
                ok = ok and m.company == emp.company
                score = score + 1
            if m.work_country:
                ok = ok and m.work_country == work_country
                score = score + 1
            if m.gender:
                ok = ok and m.gender == emp.gender
                score = score + 1
            if m.employment_type:
                ok = ok and m.employment_type == emp.employment_type
                score = score + 1
            if ok:
                key = frappe.utils.cint(m.priority) * 10 + score
                if key > best_key:
                    best_key = key
                    best = m
        return best

    def assign(emp):
        if not emp.date_of_joining:
            return "Employee has no joining date."
        if frappe.db.exists("Leave Policy Assignment", {"employee": emp.name, "docstatus": ["!=", 2]}):
            return "Employee already has a Leave Policy Assignment."
        m = find_policy(emp)
        if not m:
            return "No Leave Policy Mapping matches this employee (vendor, company, country, gender, employment type)."
        start = frappe.utils.getdate(emp.date_of_joining)
        lpa = frappe.get_doc({"doctype": "Leave Policy Assignment", "employee": emp.name, "leave_policy": m.leave_policy, "assignment_based_on": "", "effective_from": start, "effective_to": frappe.utils.add_days(frappe.utils.add_months(start, 12), -1)})
        lpa.insert(ignore_permissions=True)
        lpa.submit()
        return "Assigned " + m.leave_policy + " (" + m.name + ")"

    if doc.status == "Active" and doc.date_of_joining:
        try:
            msg = assign(doc)
            if msg.startswith("Assigned"):
                doc.add_comment("Comment", "Leave policy: " + msg)
        except Exception:
            frappe.log_error(title="Leave policy auto-assignment failed for " + doc.name)


run_script(doc)
