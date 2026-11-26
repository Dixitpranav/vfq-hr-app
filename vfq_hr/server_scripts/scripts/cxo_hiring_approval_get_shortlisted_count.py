# Server Script: CXO Hiring Approval - Get Shortlisted Count
# Type: API | API method: get_cxo_function_shortlist
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

func = frappe.form_dict.get("function")
current = frappe.form_dict.get("current") or ""
# Raises a permission error for users who cannot read CXO Hiring Approval.
frappe.get_list("CXO Hiring Approval", fields=["name"], limit_page_length=1)
eligible = []
if func:
    candidates = frappe.db.sql("""
        select ja.name, ja.applicant_name
        from `tabJob Applicant` ja
        inner join `tabJob Opening` jo on jo.name = ja.job_title
        inner join `tabJob Requisition` jr on jr.name = jo.job_requisition
        where ja.custom_recruitment_status = 'Shortlisted'
          and jo.custom_function = %(func)s
    """, {"func": func}, as_dict=True)
    for cand in candidates:
        other = frappe.db.sql("""
            select capp.parent
            from `tabCXO Hiring Approval Applicant` capp
            inner join `tabCXO Hiring Approval` cxo on cxo.name = capp.parent
            where capp.job_applicant = %(ja)s
              and capp.parent != %(me)s
              and cxo.workflow_state != 'Rejected'
        """, {"ja": cand.name, "me": current}, as_dict=True)
        if not other:
            eligible.append(cand.applicant_name or cand.name)
frappe.response["message"] = {"count": len(eligible), "applicants": eligible}
