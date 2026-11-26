# Server Script: Employee - Notify HR Ops to Activate
# Type: DocType Event | DocType: Employee | Event: After Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.custom_activation_status == "To be activated":
    link = frappe.utils.get_url_to_form("Employee", doc.name)
    app = frappe.db.get_value("Job Applicant", doc.job_applicant, ["name", "email_id", "phone_number", "custom_vendor", "job_title", "custom_cv_received_date", "custom_shortlisting_confirmation_date"], as_dict=True) if doc.job_applicant else None
    vendor = doc.get("custom_vendor") or (app.custom_vendor if app else None)
    vendor_name = (frappe.db.get_value("Supplier", vendor, "supplier_name") if vendor else None) or vendor or "Direct hire"
    manager = frappe.db.get_value("Employee", doc.reports_to, "employee_name") if doc.reports_to else ""
    cxo_on = None
    if doc.get("custom_cxo_approval"):
        cxo_on = frappe.db.get_value("CXO Hiring Approval", doc.custom_cxo_approval, "ceo_approved_on")
    def fd(d):
        return frappe.utils.formatdate(d) if d else "-"
    rows = [["Employee", doc.name], ["Name", doc.employee_name], ["Personal Email", doc.personal_email or (app.email_id if app else "")], ["Official Email (VFQ)", doc.company_email or "Not created yet"], ["Mobile", doc.cell_number or (app.phone_number if app else "")],
        ["Company", doc.company], ["Designation", doc.designation], ["Department", doc.department], ["Reports To", manager], ["Employment Type", doc.employment_type], ["Vendor", vendor_name],
        ["Job Applicant", doc.job_applicant], ["Job Opening", app.job_title if app else ""], ["CV Received", fd(app.custom_cv_received_date) if app else "-"], ["CXO Approved On", fd(cxo_on)], ["Date of Joining", fd(doc.date_of_joining)], ["Record Created On", fd(frappe.utils.today())]]
    table = "<table cellpadding='4' style='border-collapse:collapse'>"
    for r in rows:
        table += "<tr><td style='color:#6b7280'>" + r[0] + "</td><td><b>" + frappe.utils.escape_html(str(r[1] or "-")) + "</b></td></tr>"
    table += "</table><p><a href='" + link + "'>Open employee record " + doc.name + "</a></p>"

    def role_users(role):
        us = frappe.get_all("Has Role", filters={"role": role, "parenttype": "User"}, pluck="parent")
        us = frappe.get_all("User", filters={"name": ["in", us or ["__none__"]], "enabled": 1}, pluck="name")
        return [u for u in us if u not in ("Administrator", "Guest")]

    def notify(users, subject, body, d):
        if not users:
            return
        try:
            frappe.sendmail(recipients=users, subject=subject, message=body, reference_doctype="Employee", reference_name=d.name, now=False)
        except Exception:
            pass
        for u in users:
            frappe.get_doc({"doctype": "Notification Log", "for_user": u, "type": "Alert", "document_type": "Employee", "document_name": d.name, "subject": subject, "email_content": body}).insert(ignore_permissions=True)

    notify(role_users("HR Ops"), "Onboarding: new employee to activate - " + (doc.employee_name or doc.name),
        "<p>A new employee record has been created from onboarding and is <b>To be activated</b> (saved as Inactive until then).</p><p>Please check the details, complete any missing personal fields, make sure the <b>Official Email (VFQ)</b> is filled in, then click <b>Activate</b>. Activation emails the COI form to the employee.</p>" + table, doc)
    notify(role_users("HR Ops - VFQ Email"), "Create VFQ email ID: " + (doc.employee_name or doc.name) + " (" + doc.name + ")",
        "<p>Please create a VFQ email ID for the new employee below and enter it in <b>Official Email (VFQ)</b> on the employee record. The employee cannot be activated until it is filled in.</p>" + table, doc)
