# Server Script: CXO Hiring Approval - Require Joining Details
# Type: DocType Event | DocType: CXO Hiring Approval | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Blocks a CXO Hiring Approval from being sent for approval or approved while any applicant in
# the batch is missing joining details. Drafts and rejections are not blocked, and batches that
# were already Approved are left alone.
# Plain loops on purpose: comprehensions can't see local variables in a Server Script.

if doc.workflow_state in ("Pending Head of OD Approval", "Pending CHRO Approval", "Pending CAO Approval", "Pending CEO Approval", "Approved", "Approved to onboard"):
    before = doc.get_doc_before_save()
    if not (before and before.workflow_state in ("Approved", "Approved to onboard")):
        problems = []
        for row in doc.applicants:
            values = frappe.db.get_value(
                "Job Applicant",
                row.job_applicant,
                ["applicant_name", "custom_joining_date", "custom_current_company", "custom_current_notice_period"],
                as_dict=True
            )
            if values:
                missing = []
                if not values.custom_joining_date:
                    missing.append("Tentative Date of Joining")
                if not values.custom_current_company:
                    missing.append("Current Company")
                if not values.custom_current_notice_period:
                    missing.append("Current Notice Period")
                if missing:
                    problems.append(f"{values.applicant_name} ({row.job_applicant}): " + ", ".join(missing))
        if problems:
            frappe.throw(
                "Complete these applicants' joining details before CXO approval:<br>" + "<br>".join(problems),
                title="Joining Details Required"
            )
