# Server Script: File - Capture Signed COI Reply
# Type: DocType Event | DocType: File | Event: After Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.attached_to_doctype == "Communication" and doc.attached_to_name and not doc.is_folder:
    c = frappe.db.get_value("Communication", doc.attached_to_name, ["reference_doctype", "reference_name", "sent_or_received", "subject"], as_dict=True)
    if c and c.sent_or_received == "Received" and c.reference_doctype == "Employee" and c.reference_name:
        emp = frappe.db.get_value("Employee", c.reference_name, ["name", "employee_name", "custom_coi_trigger_date", "custom_coi_status"], as_dict=True)
        subj = (c.subject or "").lower()
        fname = doc.file_name or ""
        ext = fname.split(".")[-1].lower() if "." in fname else ""
        allowed = ext in ("pdf", "doc", "docx", "jpg", "jpeg", "png", "heic", "tif", "tiff")
        tiny_image = ext in ("jpg", "jpeg", "png") and (doc.file_size or 0) < 15000
        if emp and allowed and not tiny_image and ("conflict of interest" in subj or "coi" in subj or emp.custom_coi_status in ("Sent", "Sending Failed")):
            trig = str(emp.custom_coi_trigger_date or frappe.utils.today())
            base = (emp.employee_name or emp.name) + "_" + emp.name + "_COI_" + trig
            n = frappe.db.count("File", {"attached_to_doctype": "Employee", "attached_to_name": emp.name, "file_name": ["like", base + "%"]})
            new_name = base + ("_" + str(n + 1) if n else "") + "." + ext
            frappe.get_doc({"doctype": "File", "file_url": doc.file_url, "file_name": new_name, "attached_to_doctype": "Employee", "attached_to_name": emp.name, "folder": "Home/COI", "is_private": 1}).insert(ignore_permissions=True)
            frappe.db.set_value("Employee", emp.name, {"custom_coi_status": "Received", "custom_coi_received_on": frappe.utils.now(), "custom_coi_form": doc.file_url, "custom_coi_note": "Signed COI received by email and filed as " + new_name}, update_modified=False)
            ops = frappe.get_all("Has Role", filters={"role": "HR Ops", "parenttype": "User"}, pluck="parent")
            ops = frappe.get_all("User", filters={"name": ["in", ops or ["__none__"]], "enabled": 1}, pluck="name")
            for u in ops:
                if u not in ("Administrator", "Guest"):
                    frappe.get_doc({"doctype": "Notification Log", "for_user": u, "type": "Alert", "document_type": "Employee", "document_name": emp.name, "subject": "Signed COI received: " + (emp.employee_name or emp.name), "email_content": "Filed as " + new_name + " in Home/COI and attached to the employee record."}).insert(ignore_permissions=True)
