# Server Script: Job Applicant - Require Joining Details
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Blocks a Job Applicant from reaching "Approved to onboard" or "Onboarded" until the joining
# details are filled. The form also marks these fields mandatory while the applicant is in
# Shortlisted or Approved to onboard; workflow actions skip that form check, so it is enforced here.
# Applicants already Onboarded before this rule existed stay editable.
# Plain loops on purpose: comprehensions can't see local variables in a Server Script.

state = doc.custom_recruitment_status

if state in ("Approved to onboard", "Onboarded"):
    before = doc.get_doc_before_save()
    moved = (not before) or before.custom_recruitment_status != state
    if moved or state == "Approved to onboard":
        missing = []
        if not doc.custom_joining_date:
            missing.append("Tentative Date of Joining")
        if not doc.custom_current_company:
            missing.append("Current Company")
        if not doc.custom_current_notice_period:
            missing.append("Current Notice Period")
        if missing:
            frappe.throw(
                f"{doc.applicant_name} cannot move to \"{state}\" yet. Fill in: " + ", ".join(missing) + ".",
                title="Joining Details Required"
            )
