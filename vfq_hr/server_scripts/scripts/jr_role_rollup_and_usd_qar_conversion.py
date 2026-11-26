# Server Script: JR Role Rollup and USD-QAR Conversion
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

rate = frappe.db.get_value(
    "Currency Exchange",
    {"from_currency": "USD", "to_currency": "QAR", "date": ["<=", frappe.utils.nowdate()]},
    "exchange_rate",
    order_by="date desc"
) or 3.64

total_positions = 0
total_estimated_cost_usd = 0
role_labels = []

for row in (doc.get("custom_roles") or []):
    total_positions += frappe.utils.flt(row.no_of_positions)
    total_estimated_cost_usd += frappe.utils.flt(row.estimated_cost_usd) * frappe.utils.flt(row.no_of_positions)

    label = row.role_title or row.designation
    if label and label not in role_labels:
        role_labels.append(label)

    row.estimated_cost_qar = frappe.utils.flt(row.estimated_cost_usd) * rate

    # Row-level totals: per-head cost x number of positions for this row
    row.total_estimated_cost_usd = frappe.utils.flt(row.estimated_cost_usd) * frappe.utils.flt(row.no_of_positions)
    row.total_estimated_cost_qar = frappe.utils.flt(row.estimated_cost_qar) * frappe.utils.flt(row.no_of_positions)

    if row.role_type in ("Existing Role", "Replacement"):
        had_value_already = bool(row.existing_cost_usd)
        onboarded_matches = frappe.db.sql("""
            select ja.name as applicant, ja.custom_agreed_salary, ja.custom_employee, ja.modified
            from `tabJob Applicant` ja
            where ja.custom_recruitment_status = 'Onboarded'
              and ja.custom_employee_created = 1
              and ja.designation = %(designation)s
              and ifnull(ja.custom_department, '') = %(sub_function)s
              and ifnull(ja.custom_agreed_salary, 0) > 0
            order by ja.modified desc
            limit 2
        """, {
            "designation": row.designation or "",
            "sub_function": row.sub_function or ""
        }, as_dict=True)

        if len(onboarded_matches) >= 1:
            salaries = [frappe.utils.flt(m.custom_agreed_salary) for m in onboarded_matches]
            avg_cost = sum(salaries) / len(salaries)
            if not had_value_already:
                row.existing_cost_usd = avg_cost
            names = ", ".join(m.applicant for m in onboarded_matches)
            if len(onboarded_matches) >= 2:
                row.existing_cost_source_summary = (
                    f"Auto-fetched as the average Agreed Salary of the last {len(onboarded_matches)} onboarded "
                    f"candidates matched on Designation = '{row.designation}' and Sub Function = '{row.sub_function or ''}': "
                    f"{names} (individual values: {salaries}). Average = {avg_cost}. "
                    + ("You had also entered a value manually, so your manual entry was kept instead of the fetched one." if had_value_already else "This average was used to fill Existing Cost (USD) above.")
                )
            else:
                row.existing_cost_source_summary = (
                    f"Only one onboarded candidate found so far matched on Designation = '{row.designation}' and "
                    f"Sub Function = '{row.sub_function or ''}': {names} (value: {salaries[0]}). "
                    + ("You had also entered a value manually, so your manual entry was kept instead of the fetched one." if had_value_already else "This single value was used to fill Existing Cost (USD) above -- it will switch to a 2-candidate average once a second candidate onboards for this role.")
                )
        else:
            row.existing_cost_source_summary = (
                f"No onboarding history found to auto-calculate Existing Cost for Designation = '{row.designation}' "
                f"and Sub Function = '{row.sub_function or ''}'. Existing Cost (USD) "
                + ("was entered manually on this row." if had_value_already else "is currently 0 -- enter it manually, or onboard a candidate for this role to enable auto-fetch.")
            )

        if row.role_type == "Replacement":
            reason_note = row.replacement_details or "not specified yet -- add it in the Replacement / Requirement Details field"
            row.existing_cost_source_summary = row.existing_cost_source_summary + (
                f" [Role Type: Replacement -- same Existing Cost calculation as an Existing Role is used; "
                f"the only difference is the reason for replacement: {reason_note}.]"
            )

        row.existing_cost_qar = frappe.utils.flt(row.existing_cost_usd) * rate

        if frappe.utils.flt(row.no_of_positions) > 0:
            row.per_head_cost_usd = frappe.utils.flt(row.estimated_cost_usd)
        else:
            row.per_head_cost_usd = frappe.utils.flt(row.estimated_cost_usd)
    else:
        row.existing_cost_usd = 0
        row.existing_cost_qar = 0
        row.existing_cost_source_summary = ""

        # New Role: no incumbent cost exists, but per the original design this
        # field should still get a shot at the same hiring-history auto-estimate
        # used for Existing Role / Replacement above, before falling back to
        # whatever the user types in manually.
        if not frappe.utils.flt(row.estimated_cost_usd):
            new_role_matches = frappe.db.sql('''
                select ja.custom_agreed_salary
                from `tabJob Applicant` ja
                where ja.custom_recruitment_status = "Onboarded"
                  and ja.custom_employee_created = 1
                  and ja.designation = %(designation)s
                  and ifnull(ja.custom_department, "") = %(sub_function)s
                  and ifnull(ja.custom_agreed_salary, 0) > 0
                order by ja.modified desc
                limit 2
            ''', {
                "designation": row.designation or "",
                "sub_function": row.sub_function or ""
            }, as_dict=True)
            if new_role_matches:
                salaries_nr = [frappe.utils.flt(m.custom_agreed_salary) for m in new_role_matches]
                row.estimated_cost_usd = sum(salaries_nr) / len(salaries_nr)

        row.per_head_cost_usd = frappe.utils.flt(row.estimated_cost_usd)

    row.per_head_cost_qar = frappe.utils.flt(row.per_head_cost_usd) * rate

doc.no_of_positions = total_positions
doc.expected_compensation = total_estimated_cost_usd

# All salary/cost fields (Estimated Cost, Existing Cost, Per Head Cost) are entered as ANNUAL figures,
# so the total below is already annual — no x12 monthly-to-annual conversion needed.
doc.custom_annual_budget_impact = total_estimated_cost_usd
doc.custom_annual_budget_impact_qar = doc.custom_annual_budget_impact * rate

# Requisition Title = Workforce Plan ID + the positions in this requisition, comma separated
if role_labels:
    title = ", ".join(role_labels)
else:
    title = doc.custom_sub_function or doc.custom_function or "Job Requisition"
if doc.get("custom_budget_plan"):
    title = doc.custom_budget_plan + " - " + title
doc.custom_requisition_title = title[:140]
