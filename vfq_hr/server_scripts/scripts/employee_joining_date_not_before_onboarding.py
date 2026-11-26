# Server Script: Employee - Joining Date Not Before Onboarding
# Type: DocType Event | DocType: Employee | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Joining date can never be earlier than the day the candidate was onboarded (the day the Job Applicant
# moved to Onboarded and this employee record was created). Checked only when the date is changed.
def run_script(doc):
    if doc.is_new() or not doc.date_of_joining:
        return
    before = doc.get_doc_before_save()
    if not before or str(before.date_of_joining or "") == str(doc.date_of_joining or ""):
        return
    applicant = doc.get("job_applicant")
    if not applicant:
        return
    onboarded = frappe.db.get_value("Job Applicant", applicant, "custom_onboarded_date")
    if not onboarded:
        onboarded = doc.creation
    floor = frappe.utils.getdate(onboarded)
    if frappe.utils.getdate(doc.date_of_joining) < floor:
        frappe.throw(
            f"Date of Joining cannot be earlier than {frappe.utils.formatdate(floor)}. That is the day candidate {applicant} was marked Onboarded and this employee record was created. Please choose {frappe.utils.formatdate(floor)} or a later date.",
            title="Invalid Date of Joining",
        )

run_script(doc)
