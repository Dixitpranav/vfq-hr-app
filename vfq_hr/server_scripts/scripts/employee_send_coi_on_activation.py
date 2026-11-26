# Server Script: Employee - Send COI on Activation
# Type: DocType Event | DocType: Employee | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

old = doc.get_doc_before_save()
if doc.status == "Active" and old and old.status != "Active" and doc.custom_coi_status not in ("Sent", "Received"):
    tmpl = frappe.db.get_single_value("HR Settings", "custom_coi_email_template") or "Employee COI Declaration"
    form_url = frappe.db.get_single_value("HR Settings", "custom_coi_form_template")
    recipient = (doc.company_email or doc.user_id or "").strip()
    coi_status = "Sending Failed"
    coi_note = ""
    if not recipient:
        coi_note = "No Official Email (VFQ) on the employee record."
    elif not frappe.db.exists("Email Template", tmpl):
        coi_note = "COI email template " + tmpl + " not found (HR Settings)."
    else:
        et = frappe.get_doc("Email Template", tmpl)
        subject = frappe.render_template(et.subject, {"doc": doc})
        message = frappe.render_template(et.response_html or et.response, {"doc": doc})
        attachments = []
        if form_url:
            fid = frappe.db.get_value("File", {"file_url": form_url, "attached_to_name": ["is", "set"]}, "name") or frappe.db.get_value("File", {"file_url": form_url}, "name")
            if fid:
                attachments.append(fid)
        try:
            frappe.call("frappe.core.doctype.communication.email.make", doctype="Employee", name=doc.name, subject=subject, content=message, recipients=recipient, communication_medium="Email", send_email=1, attachments=attachments)
            coi_status = "Sent"
            coi_note = "COI form emailed to " + recipient + " on " + frappe.utils.formatdate(frappe.utils.today()) + ". Waiting for the signed copy by reply."
        except Exception as e:
            coi_note = "COI email could not be sent: " + str(e)[:300]
    frappe.db.set_value("Employee", doc.name, {"custom_coi_status": coi_status, "custom_coi_trigger_date": frappe.utils.today(), "custom_coi_sent_to": recipient, "custom_coi_note": coi_note}, update_modified=False)
    if coi_status != "Sent":
        ops = frappe.get_all("Has Role", filters={"role": "HR Ops", "parenttype": "User"}, pluck="parent")
        ops = frappe.get_all("User", filters={"name": ["in", ops or ["__none__"]], "enabled": 1}, pluck="name")
        for u in ops:
            if u not in ("Administrator", "Guest"):
                frappe.get_doc({"doctype": "Notification Log", "for_user": u, "type": "Alert", "document_type": "Employee", "document_name": doc.name, "subject": "COI email not sent: " + (doc.employee_name or doc.name), "email_content": coi_note}).insert(ignore_permissions=True)
