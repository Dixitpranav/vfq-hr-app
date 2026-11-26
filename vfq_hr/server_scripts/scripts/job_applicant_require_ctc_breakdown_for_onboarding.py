# Server Script: Job Applicant - Require CTC Breakdown for Onboarding
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Before an applicant moves to "Approved to onboard" (including when the CEO's final approval moves them),
# the CTC breakdown must be complete and must equal the Agreed Salary. Allowance or Benefits may be 0.
if doc.custom_recruitment_status == "Approved to onboard":
    before = doc.get_doc_before_save()
    if (not before) or before.custom_recruitment_status != "Approved to onboard":
        flt = frappe.utils.flt
        who = doc.applicant_name or doc.name
        agreed = flt(doc.custom_agreed_salary)
        basic = flt(doc.custom_ctc_basic)
        allowance = flt(doc.custom_ctc_allowance)
        benefits = flt(doc.custom_ctc_benefits)
        ctc = basic + allowance + benefits
        if not agreed:
            frappe.throw(who + ": enter the Agreed Salary before moving to Approved to onboard.", title="Agreed Salary required")
        if not basic:
            frappe.throw(who + ": enter the Basic salary in the CTC Breakdown before moving to Approved to onboard.", title="CTC breakdown incomplete")
        if abs(ctc - agreed) > 0.5:
            frappe.throw(who + ": the CTC Breakdown does not match the Agreed Salary.<br><br>Basic " + frappe.utils.fmt_money(basic) + " + Allowance " + frappe.utils.fmt_money(allowance) + " + Benefits " + frappe.utils.fmt_money(benefits) + " = <b>" + frappe.utils.fmt_money(ctc) + "</b><br>Agreed Salary = <b>" + frappe.utils.fmt_money(agreed) + "</b><br><br>Correct the breakdown (enter 0 where a part does not apply) and try again.", title="CTC does not match Agreed Salary")
