# Server Script: Block Direct Entry to Approved to Onboard
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Blocks a Job Applicant from being set to "Approved to onboard" unless it is genuinely happening
# as part of a fully-Approved CXO Hiring Approval (i.e. pushed by the
# "CXO Hiring Approval - Validate and Rollup" script itself). That script marks the document with
# doc.flags.cxo_approved_push = True right before saving, so this only blocks everyone else --
# direct field edits, the restricted workflow action, bulk edit, API calls, etc.

if doc.custom_recruitment_status == "Approved to onboard" and not doc.flags.get("cxo_approved_push"):
    covering = frappe.db.sql("""
        select capp.parent, cxo.workflow_state
        from `tabCXO Hiring Approval Applicant` capp
        inner join `tabCXO Hiring Approval` cxo on cxo.name = capp.parent
        where capp.job_applicant = %(name)s
        order by cxo.creation desc
        limit 1
    """, {"name": doc.name}, as_dict=True)

    if not covering or covering[0].workflow_state not in ("Approved", "Approved to onboard"):
        frappe.throw(
            f"{doc.applicant_name} cannot be set to \"Approved to onboard\" directly. This status is only "
            f"set automatically once a CXO Hiring Approval covering this applicant has been fully Approved "
            f"by CAO and CEO. Raise a CXO Hiring Approval for {doc.applicant_name} and get it approved first.",
            title="CXO Approval Required"
        )
