# Server Script: Fetch Existing Cost for Role
# Type: API | API method: fetch_existing_cost_for_role
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Shared "Fetch Existing Cost" lookup, callable from both Workforce Plan Position and
# Job Requisition Role rows via their "Fetch Existing Cost" button.
#
# Reuses the EXACT same matching logic as the existing automatic auto-estimate that already
# runs on Job Requisition save ("JR Role Rollup and USD-QAR Conversion"): last 2 Onboarded
# Job Applicants matched on Designation + Sub Function, averaged. Nothing in that existing
# script is touched or duplicated in behavior -- this is a read-only lookup, callable on demand.
#
# Params (frappe.form_dict): designation, sub_function
# Response: {found, existing_cost_usd, summary, match_count}

designation = frappe.form_dict.get("designation") or ""
sub_function = frappe.form_dict.get("sub_function") or ""

fec_matches = frappe.db.sql("""
    select ja.name as applicant, ja.custom_agreed_salary
    from `tabJob Applicant` ja
    where ja.custom_recruitment_status = 'Onboarded'
      and ja.custom_employee_created = 1
      and ja.designation = %(designation)s
      and (ifnull(ja.custom_department, '') = %(sub_function)s
           or ja.custom_department in (select dp.name from `tabDepartment` dp where dp.parent_department = %(sub_function)s))
      and ifnull(ja.custom_agreed_salary, 0) > 0
    order by ja.modified desc
    limit 2
""", {"designation": designation, "sub_function": sub_function}, as_dict=True)

if len(fec_matches) >= 1:
    fec_salaries = [frappe.utils.flt(m.custom_agreed_salary) for m in fec_matches]
    fec_avg = sum(fec_salaries) / len(fec_salaries)
    fec_names = ", ".join(m.applicant for m in fec_matches)

    if len(fec_matches) >= 2:
        fec_summary = (
            f"Auto-fetched as the average Agreed Salary of the last {len(fec_matches)} onboarded "
            f"candidates matched on Designation '{designation}' and Sub Function '{sub_function}': "
            f"{fec_names} (individual values: {fec_salaries}). Average = {fec_avg}."
        )
    else:
        fec_summary = (
            f"Only one onboarded candidate found so far matched on Designation '{designation}' and "
            f"Sub Function '{sub_function}': {fec_names} (value: {fec_salaries[0]}). This single value "
            f"was used -- it will switch to a 2-candidate average once a second candidate onboards for this role."
        )

    frappe.response["message"] = {
        "found": True,
        "existing_cost_usd": fec_avg,
        "summary": fec_summary,
        "match_count": len(fec_matches)
    }
else:
    fec_summary = (
        f"No onboarding history found to auto-calculate Existing Cost for Designation '{designation}' "
        f"and Sub Function '{sub_function}'. Enter it manually, or fetch again once a candidate has been "
        f"onboarded for this role."
    )
    frappe.response["message"] = {
        "found": False,
        "existing_cost_usd": 0,
        "summary": fec_summary,
        "match_count": 0
    }
