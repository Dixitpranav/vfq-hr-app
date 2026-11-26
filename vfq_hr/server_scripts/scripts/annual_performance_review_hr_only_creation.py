# Server Script: Annual Performance Review - HR Only Creation
# Type: DocType Event | DocType: Annual Performance Review | Event: Before Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Mid-Year and Annual reviews can be created only by HR (HR User / HR Manager), one at a time or in bulk.
def run_script(doc):
    user = frappe.session.user
    if user == "Administrator" or doc.flags.ignore_permissions:
        return
    roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
    if "HR User" in roles or "HR Manager" in roles:
        return
    frappe.throw(f"Only HR (HR User or HR Manager) can create a {doc.doctype}.", title="Not Allowed")

run_script(doc)
