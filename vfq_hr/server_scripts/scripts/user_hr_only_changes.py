# Server Script: User - HR Only Changes
# Type: DocType Event | DocType: User | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# User records: only HR / System Manager may change them. Employees cannot edit their own account
# (password changes go through "Forgot Password" on the login screen). Only a System Manager can grant
# the System Manager role.
def run_script(doc):
    user = frappe.session.user
    if user in ("Administrator", "Guest"):
        return
    # Saves made by system code (ignore_permissions) such as the auto Reporting Manager role are trusted.
    if doc.flags.ignore_permissions:
        return
    roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
    is_sys = "System Manager" in roles
    is_hr = is_sys or "HR Manager" in roles or "HR User" in roles
    before = None if doc.is_new() else doc.get_doc_before_save()
    if not is_sys:
        old_roles = [r.role for r in (before.get("roles") or [])] if before else []
        for r in (doc.get("roles") or []):
            if r.role in ("System Manager", "Administrator") and r.role not in old_roles:
                frappe.throw("Only a System Manager can grant the " + r.role + " role.", title="Not Allowed")
    if is_hr or not before:
        return
    watched = ["first_name", "middle_name", "last_name", "email", "username", "language", "time_zone", "enabled", "user_type", "role_profile_name", "module_profile", "mobile_no", "phone", "gender", "birth_date", "user_image", "location", "bio", "interest", "send_welcome_email"]
    changed = []
    for f in watched:
        if str(doc.get(f) or "") != str(before.get(f) or ""):
            changed.append(f)
    if sorted([r.role for r in (doc.get("roles") or [])]) != sorted([r.role for r in (before.get("roles") or [])]):
        changed.append("roles")
    if changed:
        frappe.throw("User accounts can only be changed by HR. To change your password, use 'Forgot Password' on the login screen.", title="Not Allowed")

run_script(doc)
