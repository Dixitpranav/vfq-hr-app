# Server Script: Job Applicant - Recruitment Timeline and Logs
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

today = frappe.utils.getdate(frappe.utils.nowdate())

# Hiring Manager from the Job Requisition role row
if doc.job_title and not doc.custom_hiring_manager:
    jo = frappe.db.get_value("Job Opening", doc.job_title, ["job_requisition", "custom_role_code", "designation"], as_dict=True)
    if jo and jo.job_requisition:
        f = {"parent": jo.job_requisition, "parenttype": "Job Requisition"}
        if jo.custom_role_code:
            f["role_code"] = jo.custom_role_code
        else:
            f["designation"] = jo.designation
        hm = frappe.db.get_value("Job Requisition Role", f, "hiring_manager")
        if hm:
            doc.custom_hiring_manager = hm

# Month of Tentative Date of Joining
doc.custom_joining_month = frappe.utils.formatdate(doc.custom_joining_date, "MMM yyyy") if doc.custom_joining_date else None

# Workflow transition logs
before = doc.get_doc_before_save()
old_state = before.custom_recruitment_status if before else None
new_state = doc.custom_recruitment_status
if new_state and new_state != old_state:
    if new_state == "Interview Scheduled" and not doc.custom_interview_schedule_confirmed_date:
        doc.custom_interview_schedule_confirmed_date = frappe.utils.now_datetime()
    if new_state == "Shortlisted" and not doc.custom_shortlisting_confirmation_date:
        doc.custom_shortlisting_confirmation_date = frappe.utils.now_datetime()
    if new_state == "Onboarded" and not doc.custom_onboarded_date:
        doc.custom_onboarded_date = frappe.utils.now_datetime()

# Ageing: Role sharing date to Onboarded date (or today)
if doc.custom_role_sharing_date:
    end = frappe.utils.getdate(doc.custom_onboarded_date) if doc.custom_onboarded_date else today
    doc.custom_ageing_days = frappe.utils.date_diff(end, frappe.utils.getdate(doc.custom_role_sharing_date))
else:
    doc.custom_ageing_days = 0

# Total recruitment expense
flt = frappe.utils.flt
doc.custom_total_recruitment_expense = flt(doc.custom_recruitment_fee) + flt(doc.custom_notice_period_buyout) + flt(doc.custom_joining_bonus) + flt(doc.custom_recruitment_agency_charges) + flt(doc.custom_background_verification_charges)

# CTC breakdown check against Agreed Salary (warning only)
parts = flt(doc.custom_ctc_basic) + flt(doc.custom_ctc_allowance) + flt(doc.custom_ctc_benefits)
if parts and flt(doc.custom_agreed_salary) and abs(parts - flt(doc.custom_agreed_salary)) > 0.5:
    frappe.msgprint("Basic + Allowance + Benefits (" + frappe.utils.fmt_money(parts) + ") does not match Agreed Salary (" + frappe.utils.fmt_money(doc.custom_agreed_salary) + ").", title="CTC breakdown check", indicator="orange")
