# Server Script: Log Activity on Job Applicant Backed-Off
# Type: DocType Event | DocType: Job Applicant | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Logs an Activity/Comment entry when a Job Applicant is marked Backed-Off, recording
# which pipeline stage they backed off from. Backed-Off is a terminal, non-active status
# (mechanically like Rejected) -- it never reaches Onboarded, so it has no impact on
# committed/consumed headcount on the Workforce Plan or Job Requisition (those are only
# touched by requisition approval and by the onboarding script respectively). The position
# itself remains open/pending for a new candidate once this applicant drops out of the
# active pipeline.
if doc.custom_recruitment_status == "Backed-Off":
    previous = doc.get_doc_before_save()
    prev_status = previous.custom_recruitment_status if previous else None
    if prev_status != "Backed-Off":
        doc.add_comment(
            "Info",
            "Candidate marked as Backed-Off (previous status: " + (prev_status or "Unknown") + "). "
            "This applicant is no longer active in the recruitment pipeline; the position remains "
            "open/pending for a new candidate. No impact on committed or consumed headcount."
        )
