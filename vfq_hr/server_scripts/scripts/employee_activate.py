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

# VFQ email request to the HR Ops - VFQ Email group
users = frappe.get_all("Has Role", filters={"role": "HR Ops - VFQ Email", "parenttype": "User"}, pluck="parent")
users = frappe.get_all("User", filters={"name": ["in", users or ["__none__"]], "enabled": 1}, pluck="name")
users = [u for u in users if u not in ("Administrator", "Guest")]
app = frappe.db.get_value("Job Applicant", doc.job_applicant, ["name", "applicant_name", "email_id", "phone_number", "custom_vendor", "job_title"], as_dict=True) if doc.job_applicant else None
vendor = doc.get("custom_vendor") or (app.custom_vendor if app else None)
vendor_name = frappe.db.get_value("Supplier", vendor, "supplier_name") if vendor else None
rows = [["Employee ID", doc.name], ["Full Name", doc.employee_name], ["First / Last Name", (doc.first_name or "") + " / " + (doc.last_name or "")], ["Company", doc.company], ["Designation", doc.designation], ["Department", doc.department],
    ["Reports To", (frappe.db.get_value("Employee", doc.reports_to, "employee_name") if doc.reports_to else "")], ["Date of Joining", frappe.utils.formatdate(doc.date_of_joining) if doc.date_of_joining else ""], ["Employment Type", doc.employment_type],
    ["Personal Email", doc.personal_email or (app.email_id if app else "")], ["Mobile", doc.cell_number or (app.phone_number if app else "")], ["Job Applicant", app.name if app else ""], ["Job Opening", app.job_title if app else ""],
    ["Vendor", (vendor_name or vendor or "Direct hire")], ["Project", doc.get("custom_project")]]
link = frappe.utils.get_url_to_form("Employee", doc.name)
subject = "Create VFQ email ID: " + (doc.employee_name or doc.name) + " (" + doc.name + ")"
body = "<p>The employee below has been activated. Please create a VFQ email ID, then enter it in <b>Company Email</b> on the employee record and save. The system user will be created and linked automatically.</p><table cellpadding='4' style='border-collapse:collapse'>"
for r in rows:
    body += "<tr><td style='color:#6b7280'>" + r[0] + "</td><td><b>" + frappe.utils.escape_html(str(r[1] or "-")) + "</b></td></tr>"
body += "</table><p><a href='" + link + "'>Open employee record</a></p>"
if users:
    try:
        frappe.sendmail(recipients=users, subject=subject, message=body, reference_doctype="Employee", reference_name=doc.name, now=False)
    except Exception:
        pass
    for u in users:
        frappe.get_doc({"doctype": "Notification Log", "for_user": u, "type": "Alert", "document_type": "Employee", "document_name": doc.name, "subject": subject, "email_content": body}).insert(ignore_permissions=True)
frappe.response["message"] = {"status": doc.custom_activation_status, "notified": len(users)}
