# Server Script: Job Applicant - Carry Position From Job Opening
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Position (the Job Requisition Role) always comes from the Job Opening: Workforce Plan > Job Requisition > Job Opening.
before = doc.get_doc_before_save()
opening_changed = before and before.job_title != doc.job_title
if doc.job_title and (not doc.custom_position or opening_changed):
    opening_info = frappe.db.get_value("Job Opening", doc.job_title, ["job_requisition", "designation", "custom_role_code"], as_dict=True)
    if opening_info and opening_info.job_requisition:
        matches = []
        if opening_info.custom_role_code:
            matches = frappe.get_all("Job Requisition Role", filters={"parent": opening_info.job_requisition, "role_code": opening_info.custom_role_code}, fields=["name"], limit=1)
        if not matches:
            matches = frappe.get_all("Job Requisition Role", filters={"parent": opening_info.job_requisition, "designation": opening_info.designation}, fields=["name"], limit=1)
        if matches:
            doc.custom_position = matches[0].name
if doc.job_title and not doc.custom_position:
    frappe.throw("Position could not be found for Job Opening " + doc.job_title + ". Check that the opening is linked to an approved Job Requisition.", title="Position Not Found")
