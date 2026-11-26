# Server Script: Employee - Notify HR Ops to Activate
# Type: DocType Event | DocType: Employee | Event: After Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.custom_activation_status == "To be activated":
    users = frappe.get_all("Has Role", filters={"role": "HR Ops", "parenttype": "User"}, pluck="parent")
    users = frappe.get_all("User", filters={"name": ["in", users or ["__none__"]], "enabled": 1}, pluck="name")
    users = [u for u in users if u not in ("Administrator", "Guest")]
    if users:
        link = frappe.utils.get_url_to_form("Employee", doc.name)
        subject = "New employee to activate: " + (doc.employee_name or doc.name)
        rows = [["Employee", doc.name], ["Name", doc.employee_name], ["Company", doc.company], ["Designation", doc.designation], ["Department", doc.department], ["Date of Joining", frappe.utils.formatdate(doc.date_of_joining) if doc.date_of_joining else ""], ["Job Applicant", doc.job_applicant], ["Vendor", doc.get("custom_vendor")]]
        body = "<p>A new employee record has been created from onboarding and is <b>To be activated</b> (saved as Inactive until then).</p><p>Please check the details, complete any missing personal fields and click <b>Activate</b> on the record.</p><table cellpadding='4' style='border-collapse:collapse'>"
        for r in rows:
            body += "<tr><td style='color:#6b7280'>" + r[0] + "</td><td><b>" + frappe.utils.escape_html(str(r[1] or "-")) + "</b></td></tr>"
        body += "</table><p><a href='" + link + "'>Open employee record</a></p>"
        try:
            frappe.sendmail(recipients=users, subject=subject, message=body, reference_doctype="Employee", reference_name=doc.name, now=False)
        except Exception:
            pass
        for u in users:
            frappe.get_doc({"doctype": "Notification Log", "for_user": u, "type": "Alert", "document_type": "Employee", "document_name": doc.name, "subject": subject, "email_content": body}).insert(ignore_permissions=True)
