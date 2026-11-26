# Server Script: Job Opening - One Opening Per Role and Locked Count
# Type: DocType Event | DocType: Job Opening | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.job_requisition:
    filters = {"job_requisition": doc.job_requisition, "name": ["!=", doc.name or ""]}
    if doc.custom_role_code:
        filters["custom_role_code"] = doc.custom_role_code
    else:
        filters["designation"] = doc.designation
    other = frappe.db.get_value("Job Opening", filters, "name")
    if other:
        frappe.throw("A Job Opening (" + other + ") already exists for this role on Job Requisition " + doc.job_requisition + ". Only one Job Opening is allowed per role.", title="Duplicate Job Opening")

if not doc.is_new():
    before = doc.get_doc_before_save()
    if before and (frappe.utils.cint(before.vacancies) != frappe.utils.cint(doc.vacancies) or frappe.utils.cint(before.planned_vacancies) != frappe.utils.cint(doc.planned_vacancies)):
        frappe.throw("The number of positions comes from the Job Requisition and cannot be changed on the Job Opening.", title="Locked")
