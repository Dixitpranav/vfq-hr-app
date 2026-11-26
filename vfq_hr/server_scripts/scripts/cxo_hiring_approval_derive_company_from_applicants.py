# Server Script: CXO Hiring Approval - Derive Company from Applicants
# Type: DocType Event | DocType: CXO Hiring Approval | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

companies = set()
for row in (doc.applicants or []):
    if row.job_applicant:
        c = frappe.db.get_value('Job Applicant', row.job_applicant, 'custom_company')
        if c:
            companies.add(c)

if len(companies) > 1:
    frappe.throw(
        'The Applicants in this CXO Hiring Approval belong to different companies ('
        + ', '.join(sorted(companies))
        + '). All applicants on one CXO Hiring Approval must belong to the same company.'
    )
elif len(companies) == 1:
    doc.company = list(companies)[0]
