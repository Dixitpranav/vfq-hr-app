# Server Script: Job Applicant - Joining Date Not Before Onboarding
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Once a candidate is onboarded, the joining date cannot be moved earlier than the onboarding day.
# At the moment of onboarding it cannot be in the past either.
def run_script(doc):
    if doc.is_new() or not doc.custom_joining_date:
        return
    before = doc.get_doc_before_save()
    if not before:
        return
    was_onboarded = before.custom_onboarded_date
    now_onboarded = doc.custom_onboarded_date or doc.custom_recruitment_status == "Onboarded"
    if not was_onboarded and not now_onboarded:
        return
    date_changed = str(before.custom_joining_date or "") != str(doc.custom_joining_date or "")
    becoming_onboarded = (not was_onboarded) and now_onboarded
    if not date_changed and not becoming_onboarded:
        return
    floor = frappe.utils.getdate(was_onboarded or doc.custom_onboarded_date or frappe.utils.nowdate())
    if frappe.utils.getdate(doc.custom_joining_date) < floor:
        if was_onboarded:
            reason = f"the day this candidate was marked Onboarded and their employee record ({doc.custom_employee or 'linked employee'}) was created"
        else:
            reason = "today, the day this candidate is being onboarded"
        frappe.throw(
            f"Joining Date cannot be earlier than {frappe.utils.formatdate(floor)}. That is {reason}. Please choose {frappe.utils.formatdate(floor)} or a later date.",
            title="Invalid Joining Date",
        )

run_script(doc)
