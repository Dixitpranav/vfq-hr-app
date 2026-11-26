# Server Script: Job Applicant - Require Reports To With Clear Message
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Give a clear, actionable message when the applicant has no Reports To.
if doc.job_title:
    reports_to_value = doc.custom_reports_to or frappe.db.get_value("Job Opening", doc.job_title, "custom_reports_to")
    if not reports_to_value:
        frappe.throw(
            "Reports To is missing. It is filled manually on the Job Opening, and it is not set on Job Opening " + str(doc.job_title) + ". Open that Job Opening, set Reports To to the hiring manager, save it, and then add the applicant.",
            title="Reports To Required"
        )
    if not doc.custom_reports_to:
        doc.custom_reports_to = reports_to_value
