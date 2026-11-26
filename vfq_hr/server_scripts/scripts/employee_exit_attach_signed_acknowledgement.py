# Server Script: Employee Exit - Attach Signed Acknowledgement
# Type: DocType Event | DocType: Employee Exit | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# After each sign-off, attach a fresh copy of the Resignation Acknowledgement PDF.
before = doc.get_doc_before_save()
changed = False
for f in ["custom_employee_signed_on", "custom_manager_signed_on", "custom_hr_signed_on"]:
    # Only when a sign-off is recorded for the first time (each sign-off happens once).
    if doc.get(f) and ((not before) or not before.get(f)):
        changed = True
if changed:
    stage = "HR-Approved" if doc.get("custom_hr_signed_on") else ("Manager-Approved" if doc.get("custom_manager_signed_on") else "Employee-Signed")
    pdf = frappe.attach_print("Employee Exit", doc.name, print_format="Resignation Acknowledgement")
    f = frappe.get_doc({"doctype": "File", "file_name": "Resignation-Acknowledgement-" + doc.name + "-" + stage + ".pdf", "attached_to_doctype": "Employee Exit", "attached_to_name": doc.name, "content": pdf.get("fcontent"), "is_private": 1})
    f.insert(ignore_permissions=True)
    doc.db_set("custom_signed_acknowledgement", f.file_url, update_modified=False)
