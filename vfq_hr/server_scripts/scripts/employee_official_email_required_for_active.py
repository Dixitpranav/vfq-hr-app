# Server Script: Employee - Official Email Required for Active
# Type: DocType Event | DocType: Employee | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

old = doc.get_doc_before_save()
becoming_active = doc.status == "Active" and (not old or old.status != "Active")
if becoming_active:
    email = (doc.company_email or "").strip().lower()
    keyword = (frappe.db.get_single_value("HR Settings", "custom_official_email_domain_keyword") or "vodafone").strip().lower()
    parts = email.split("@")
    if not email:
        frappe.throw("Enter the employee's <b>Official Email (VFQ)</b> before making the record Active. Its domain must contain <b>" + keyword + "</b> (e.g. name@" + keyword + ".qa).", title="Official email required")
    if len(parts) != 2 or not parts[0] or "." not in parts[1] or " " in email:
        frappe.throw("<b>" + email + "</b> is not a valid email address. Enter a valid Official Email (VFQ) before activating.", title="Official email required")
    if keyword and keyword not in parts[1]:
        frappe.throw("The Official Email (VFQ) domain must contain <b>" + keyword + "</b> (for example name@" + keyword + ".qa, ." + "com or .in). <b>" + email + "</b> is not allowed.", title="Official email required")
    doc.company_email = email
