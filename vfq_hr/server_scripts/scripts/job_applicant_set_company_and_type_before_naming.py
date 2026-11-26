# Server Script: Job Applicant - Set Company and Type Before Naming
# Type: DocType Event | DocType: Job Applicant | Event: Before Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# The ID series uses company and employment type, so set them from the opening before the ID is generated.
if doc.get("job_title"):
    vals = frappe.db.get_value("Job Opening", doc.job_title, ["company", "employment_type"], as_dict=True)
    if vals:
        if vals.company:
            doc.custom_company = vals.company
        if vals.employment_type:
            doc.custom_employment_type = vals.employment_type
