# Server Script: Job Applicant - One Email Per Company
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# The same email address can appear only once per company in the applicant list.
email = (doc.get("email_id") or "").strip().lower()
company = doc.get("custom_company")
if not company and doc.get("job_title"):
    company = frappe.db.get_value("Job Opening", doc.job_title, "company")
if email and company:
    clash = frappe.db.sql("select name from `tabJob Applicant` where lower(email_id) = %s and custom_company = %s and name != %s limit 1", (email, company, doc.name or ""))
    if clash:
        frappe.throw("An applicant with the email " + email + " already exists in " + company + " (" + clash[0][0] + "). Each email can be listed only once per company.", title="Duplicate Applicant Email")
