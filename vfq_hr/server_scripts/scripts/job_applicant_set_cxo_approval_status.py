# Server Script: Job Applicant - Set CXO Approval Status
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# One neutral status while a shortlisted applicant is going through CXO approval.
doc.custom_cxo_approval_status = "Awaiting Approval" if doc.custom_recruitment_status == "Shortlisted" else ""
