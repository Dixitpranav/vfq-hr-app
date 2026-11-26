# Server Script: Block Onboarding Without CXO Approval
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Blocks a Job Applicant from moving to "Onboarded" unless a CXO Hiring Approval covering
# this applicant exists and has reached the fully-Approved state (CAO + CEO sign-off).
# This is additive on top of the existing recruitment flow -- it does not change how any other
# recruitment_status transition behaves, only adds a gate on the move into "Onboarded".

if doc.custom_recruitment_status == "Onboarded":
    covering = frappe.db.sql("""
        select capp.parent, cxo.workflow_state
        from `tabCXO Hiring Approval Applicant` capp
        inner join `tabCXO Hiring Approval` cxo on cxo.name = capp.parent
        where capp.job_applicant = %(name)s
        order by cxo.creation desc
        limit 1
    """, {"name": doc.name}, as_dict=True)

    if not covering:
        frappe.throw(
            f"{doc.applicant_name} cannot be moved to \"Onboarded\" yet: no CXO Hiring Approval has been "
            f"raised for this applicant. Add {doc.applicant_name} to a CXO Hiring Approval batch and get it "
            f"approved by CAO and CEO before onboarding.",
            title="CXO Approval Required"
        )
    elif covering[0].workflow_state not in ("Approved", "Approved to onboard"):
        frappe.throw(
            f"{doc.applicant_name} cannot be moved to \"Onboarded\" yet: their CXO Hiring Approval "
            f"({covering[0].parent}) is currently \"{covering[0].workflow_state}\", not fully Approved. "
            f"It needs both CAO and CEO sign-off before onboarding can proceed.",
            title="CXO Approval Required"
        )
