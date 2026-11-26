# Server Script: Employee - Activate
# Type: API | API method: activate_employee
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

name = frappe.form_dict.get("employee")
roles = frappe.get_all("Has Role", filters={"parent": frappe.session.user, "parenttype": "User"}, pluck="role")
allowed = frappe.session.user == "Administrator" or len(set(roles) & set(["HR Ops", "HR Manager", "System Manager"])) > 0
if not allowed:
    frappe.throw("Only HR Ops, HR Manager or System Manager can activate employees.", frappe.PermissionError)
doc = frappe.get_doc("Employee", name)
if doc.custom_activation_status != "To be activated":
    frappe.throw("Employee " + name + " is not awaiting activation.")
doc.status = "Active"
doc.custom_activation_status = "Activated"
doc.custom_activated_by = frappe.session.user
doc.custom_activated_on = frappe.utils.now_datetime()
doc.flags.via_activation = True
doc.save()

# The COI form is emailed by "Employee - Send COI on Activation" (After Save).
coi = frappe.db.get_value("Employee", doc.name, ["custom_coi_status", "custom_coi_note", "user_id"], as_dict=True) or {}
frappe.response["message"] = {"status": doc.custom_activation_status, "coi_status": coi.get("custom_coi_status"), "coi_note": coi.get("custom_coi_note"), "user_id": coi.get("user_id")}
