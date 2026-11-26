# Server Script: CXO Hiring Approval - Validate and Rollup v2
# Type: DocType Event | DocType: CXO Hiring Approval | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Validates and rolls up a CXO Hiring Approval batch.
# - Each row must reference a Job Applicant that is currently "Shortlisted".
# - No applicant may appear twice in this batch, and no applicant may be in more than one
#   active (non-Rejected) CXO Hiring Approval batch at a time.
# - Snapshot fields (name, designation, function, department, project, salary) are captured
#   here rather than left as live fetch_from links, so the approval reflects the figures that
#   were actually reviewed even if the Job Applicant record changes later.
# - Totals and the USD -> QAR conversion reuse the same Currency Exchange lookup (with the
#   same 3.64 fallback) already used for Job Requisition, for consistency.
# - Runs on every save, including CAO/CEO approval clicks, so a row that stops being eligible
#   (e.g. someone else rejected that applicant elsewhere) is caught again at every stage.

rate = frappe.db.get_value(
    "Currency Exchange",
    {"from_currency": "USD", "to_currency": "QAR", "date": ["<=", frappe.utils.nowdate()]},
    "exchange_rate",
    order_by="date desc"
) or 3.64

# --- New: Functions table -> auto-add eligible Shortlisted applicants ---
# For each Function chosen in the Functions table, find every currently-Shortlisted Job
# Applicant whose Job Requisition (via Job Opening) sits under that Function -- using the same
# job_title -> Job Opening -> Job Requisition -> custom_function chain the per-row snapshot
# logic below already uses -- skip anyone already in this batch or already in another active
# (non-Rejected) CXO Hiring Approval, and auto-append the rest into the (hidden) Applicants
# table. Blocks the save if a chosen Function currently has zero eligible candidates.
existing_applicant_ids = set(r.job_applicant for r in (doc.get("applicants") or []) if r.job_applicant)

for frow in (doc.get("functions") or []):
    if not frow.function:
        continue

    candidates = frappe.db.sql("""
        select ja.name
        from `tabJob Applicant` ja
        inner join `tabJob Opening` jo on jo.name = ja.job_title
        inner join `tabJob Requisition` jr on jr.name = jo.job_requisition
        where ja.custom_recruitment_status = 'Shortlisted'
          and jo.custom_function = %(func)s
    """, {"func": frow.function}, as_dict=True)

    eligible_count = 0
    for cand in candidates:
        if cand.name in existing_applicant_ids:
            eligible_count += 1
            continue

        other_for_func = frappe.db.sql("""
            select capp.parent
            from `tabCXO Hiring Approval Applicant` capp
            inner join `tabCXO Hiring Approval` cxo on cxo.name = capp.parent
            where capp.job_applicant = %(ja)s
              and capp.parent != %(me)s
              and cxo.workflow_state != 'Rejected'
        """, {"ja": cand.name, "me": doc.name or ""}, as_dict=True)
        if other_for_func:
            continue

        cand_terms = frappe.db.get_value("Job Applicant", cand.name, ["custom_employment_type", "custom_variable_pay_type", "custom_variable_pay_basis", "custom_variable_pay_value"], as_dict=True) or {}
        doc.append("applicants", {
            "job_applicant": cand.name,
            "custom_employment_type": cand_terms.get("custom_employment_type"),
            "custom_variable_pay_type": cand_terms.get("custom_variable_pay_type") or "None",
            "custom_variable_pay_basis": cand_terms.get("custom_variable_pay_basis"),
            "custom_variable_pay_value": cand_terms.get("custom_variable_pay_value")
        })
        existing_applicant_ids.add(cand.name)
        eligible_count += 1

    frow.shortlisted_count = eligible_count

    if eligible_count == 0:
        frappe.throw(
            f"No Shortlisted applicants are currently eligible for Function \"{frow.function}\" "
            f"(either none are Shortlisted right now, or all of them are already in another active "
            f"CXO Hiring Approval batch). Remove this Function, or wait until candidates become eligible.",
            title="No Eligible Applicants for Function"
        )

rows = doc.get("applicants") or []

if doc.workflow_state and doc.workflow_state != "Draft" and not rows:
    frappe.throw(
        "This CXO Hiring Approval has no applicants in it. Add at least one Shortlisted applicant "
        "before sending it for CAO/CEO approval.",
        title="No Applicants in Batch"
    )

seen = set()
total_usd = 0

for row in rows:
    if not row.job_applicant:
        frappe.throw("Every row must reference a Job Applicant. Remove any blank rows.", title="Missing Job Applicant")

    if row.job_applicant in seen:
        frappe.throw(
            f"Job Applicant {row.job_applicant} is listed more than once in this batch. "
            f"Each applicant can appear only once per CXO Hiring Approval.",
            title="Duplicate Applicant"
        )
    seen.add(row.job_applicant)

    ja = frappe.db.get_value(
        "Job Applicant",
        row.job_applicant,
        ["applicant_name", "designation", "custom_department", "custom_project", "custom_agreed_salary",
         "custom_recruitment_status", "job_title", "custom_vendor", "custom_position", "custom_hiring_type",
         "custom_exceptional_salary_case"],
        as_dict=True
    )
    if not ja:
        frappe.throw(f"Job Applicant {row.job_applicant} could not be found.", title="Applicant Not Found")

    if ja.custom_recruitment_status != "Shortlisted":
        frappe.throw(
            f"{ja.applicant_name or row.job_applicant} is not in \"Shortlisted\" status right now "
            f"(currently \"{ja.custom_recruitment_status or 'Not Set'}\"). Only Shortlisted applicants "
            f"are eligible for CXO approval -- remove this row, or wait until they are Shortlisted.",
            title="Applicant Not Eligible"
        )

    other_batch = frappe.db.sql("""
        select capp.parent
        from `tabCXO Hiring Approval Applicant` capp
        inner join `tabCXO Hiring Approval` cxo on cxo.name = capp.parent
        where capp.job_applicant = %(ja)s
          and capp.parent != %(me)s
          and cxo.workflow_state != 'Rejected'
    """, {"ja": row.job_applicant, "me": doc.name or ""}, as_dict=True)
    if other_batch:
        frappe.throw(
            f"{ja.applicant_name or row.job_applicant} is already included in another CXO Hiring Approval "
            f"({other_batch[0].parent}) that hasn't been rejected. Remove them from that batch first, or "
            f"wait for that decision before adding them here.",
            title="Applicant Already in Another Batch"
        )

    function = None
    sub_function = None
    if ja.job_title:
        jo_data = frappe.db.get_value("Job Opening", ja.job_title, ["job_requisition", "custom_function", "custom_sub_function"], as_dict=True)
        if jo_data:
            function = jo_data.custom_function
            sub_function = jo_data.custom_sub_function
            row.job_requisition = jo_data.job_requisition

    row.applicant_name = ja.applicant_name
    row.designation = ja.designation
    row.function = function
    row.custom_sub_function = sub_function
    row.department = ja.custom_department
    row.project = ja.custom_project
    row.cxo_project_name = frappe.db.get_value("Project", ja.custom_project, "project_name") if ja.custom_project else None
    row.cxo_vendor = ja.custom_vendor
    row.agreed_salary_usd = frappe.utils.flt(ja.custom_agreed_salary)
    row.custom_agreed_salary_monthly = frappe.utils.flt(ja.custom_agreed_salary) / 12.0
    row.agreed_salary_qar = frappe.utils.flt(ja.custom_agreed_salary) * rate
    row.currency_code_usd = "USD"
    row.currency_code_qar = "QAR"
    row.position = ja.custom_position
    row.vendor = ja.custom_vendor

    total_usd += row.agreed_salary_usd

doc.total_applicants = len(rows)
doc.total_agreed_salary_usd = total_usd
doc.custom_total_agreed_salary_monthly = total_usd / 12.0
doc.total_agreed_salary_qar = total_usd * rate
doc.currency_code_usd = "USD"
doc.currency_code_qar = "QAR"
doc.exchange_rate_used = rate
doc.exchange_rate_date = frappe.utils.now_datetime()

# Record who approved at each level and when, based on the actual state transition happening
# in this save (comparing against the state the document was in before this save started).
old = doc.get_doc_before_save()
old_state = old.workflow_state if old else None

if doc.workflow_state == "Pending CHRO Approval" and old_state == "Pending Head of OD Approval":
    doc.custom_hod_approved_by = frappe.session.user
    doc.custom_hod_approved_on = frappe.utils.now_datetime()

if doc.workflow_state == "Pending CAO Approval" and old_state == "Pending CHRO Approval":
    doc.custom_chro_approved_by = frappe.session.user
    doc.custom_chro_approved_on = frappe.utils.now_datetime()

if doc.workflow_state == "Pending CEO Approval" and old_state == "Pending CAO Approval":
    doc.cao_approved_by = frappe.session.user
    doc.cao_approved_on = frappe.utils.now_datetime()

if doc.workflow_state in ("Approved", "Approved to onboard") and old_state == "Pending CEO Approval":
    doc.ceo_approved_by = frappe.session.user
    doc.ceo_approved_on = frappe.utils.now_datetime()

    # Push every covered applicant from Shortlisted to "Approved to onboard" now that CXO
    # sign-off is complete. HR still has to click "Onboard" manually from there -- this only
    # moves them one step closer, it never finalizes onboarding itself.
    for row in (doc.get("applicants") or []):
        ja_status = frappe.db.get_value("Job Applicant", row.job_applicant, "custom_recruitment_status")
        if ja_status == "Shortlisted":
            ja_doc = frappe.get_doc("Job Applicant", row.job_applicant)
            ja_doc.flags.cxo_approved_push = True
            ja_doc.custom_recruitment_status = "Approved to onboard"
            ja_doc.save(ignore_permissions=True)


# --- New: roll up validated Shortlisted rows into Standard / Exceptional approval tables ---
# Grouped by Position + Vendor + Project (a Position can be sourced through more than one
# Vendor/Project combination, so each combination gets its own row). If a group has a mix of
# standard and exceptional-salary applicants, it is split: one row in Standard for its standard
# applicants, one row in Exceptional for its exceptional ones. Does not touch the "applicants"
# table or any of the validation/snapshot/approval logic above.

# Free-text fields a human types into these two tables (HR Comments, and the pre-existing
# Recommendation from Project Team on Standard) would otherwise be silently wiped on every
# save, since both tables are fully rebuilt below. Capture whatever is there now, keyed by
# the same Position+Vendor+Project grouping used to rebuild the rows, and carry it forward.
preserved_std = {}
for r in (doc.get("standard_approvals") or []):
    preserved_std[(r.position or "", r.vendor or "", r.project or "")] = {
        "hr_comments": r.hr_comments,
        "recommendation_from_project_team": r.recommendation_from_project_team
    }

preserved_exc = {}
for r in (doc.get("exceptional_approvals") or []):
    preserved_exc[(r.position or "", r.vendor or "", r.project or "")] = {
        "hr_comments": r.hr_comments
    }

doc.set("standard_approvals", [])
doc.set("exceptional_approvals", [])

rollup_groups = {}
for row in (doc.get("applicants") or []):
    key = (row.position or "", row.vendor or "", row.project or "")
    ja_flags = frappe.db.get_value(
        "Job Applicant", row.job_applicant,
        ["custom_exceptional_salary_case", "custom_hiring_type"],
        as_dict=True
    ) or {}
    bucket = rollup_groups.setdefault(key, {"standard": [], "exceptional": []})
    if ja_flags.get("custom_exceptional_salary_case"):
        bucket["exceptional"].append(row)
    else:
        bucket["standard"].append(row)

for (position, vendor, project), bucket in rollup_groups.items():
    role = frappe.db.get_value(
        "Job Requisition Role", position,
        ["parent", "no_of_positions", "lower_salary_range", "max_salary_range", "role_classification", "custom_function", "custom_sub_function"],
        as_dict=True
    ) if position else None
    cost_line = frappe.db.get_value("Job Requisition", role.parent, "custom_budget_line") if role and role.parent else None
    function_val = role.custom_function if role else None
    sub_function_val = role.custom_sub_function if role else None
    approved_role_count = role.no_of_positions if role else None
    role_val = role.role_classification if role else None
    recommended_range = None
    if role and role.lower_salary_range and role.max_salary_range:
        recommended_range = f"{role.lower_salary_range / 12:,.0f} - {role.max_salary_range / 12:,.0f} / month"

    if bucket["standard"]:
        std_rows = bucket["standard"]
        hiring_types = set(frappe.db.get_value("Job Applicant", r.job_applicant, "custom_hiring_type") for r in std_rows)
        hiring_type_val = list(hiring_types)[0] if len(hiring_types) == 1 else "Mixed"
        monthly_cost = sum(frappe.utils.flt(r.agreed_salary_usd) for r in std_rows) / 12
        preserved_std_row = preserved_std.get((position, vendor, project), {})
        doc.append("standard_approvals", {
            "currency": "USD",
            "position": position,
            "vendor": vendor or None,
            "project": project or None,
            "hiring_type": hiring_type_val,
            "role": role_val,
            "custom_position_title": role_val or frappe.db.get_value("Job Requisition Role", position, "designation"),
            "recommended_salary_range": recommended_range,
            "approx_monthly_cost_impact": monthly_cost,
            "cost_line": cost_line,
            "custom_cost_line_name": (frappe.db.get_value("Budget", cost_line, "custom_budget_title") if cost_line else None) or cost_line,
            "custom_project_name": (frappe.db.get_value("Project", project, "project_name") if project else None) or project,
            "function": function_val,
            "custom_sub_function": sub_function_val,
            "hr_comments": preserved_std_row.get("hr_comments"),
            "recommendation_from_project_team": preserved_std_row.get("recommendation_from_project_team"),
            "shortlisted_count": len(std_rows),
            "approved_role_count": approved_role_count
        })

    if bucket["exceptional"]:
        exc_rows = bucket["exceptional"]
        hiring_types = set(frappe.db.get_value("Job Applicant", r.job_applicant, "custom_hiring_type") for r in exc_rows)
        hiring_type_val = list(hiring_types)[0] if len(hiring_types) == 1 else "Mixed"
        monthly_cost = sum(frappe.utils.flt(r.agreed_salary_usd) for r in exc_rows) / 12
        preserved_exc_row = preserved_exc.get((position, vendor, project), {})
        doc.append("exceptional_approvals", {
            "currency": "USD",
            "position": position,
            "vendor": vendor or None,
            "project": project or None,
            "type": hiring_type_val,
            "role": role_val,
            "custom_position_title": role_val or frappe.db.get_value("Job Requisition Role", position, "designation"),
            "recommended_salary_range": recommended_range,
            "cost_line": cost_line,
            "custom_cost_line_name": (frappe.db.get_value("Budget", cost_line, "custom_budget_title") if cost_line else None) or cost_line,
            "custom_project_name": (frappe.db.get_value("Project", project, "project_name") if project else None) or project,
            "function": function_val,
            "custom_sub_function": sub_function_val,
            "hr_comments": preserved_exc_row.get("hr_comments"),
            "monthly_cost_impact": monthly_cost,
            "shortlisted_count": len(exc_rows),
            "approved_role_count": approved_role_count
        })

# Warn (do not block) if shortlisted count across both tables for a position exceeds the
# approved Role Count on that position -- HR/CXO can still proceed, but should notice.
for (position, vendor, project), bucket in rollup_groups.items():
    total_shortlisted = len(bucket["standard"]) + len(bucket["exceptional"])
    approved_role_count = frappe.db.get_value("Job Requisition Role", position, "no_of_positions") if position else None
    if approved_role_count and total_shortlisted > approved_role_count:
        frappe.msgprint(
            f"Position {position}: {total_shortlisted} Shortlisted applicant(s) exceed the approved Role Count ({approved_role_count}). "
            f"You can still proceed, but please confirm this is expected.",
            title="Role Count Exceeded", indicator="orange", alert=True
        )


# --- Workforce Plan Summary (for CAO/CEO) -----------------------------------
def wps_money(val):
    # Built without str.format(), which the Server Script sandbox does not allow.
    amount = int(round(frappe.utils.flt(val)))
    sign = "-" if amount < 0 else ""
    digits = str(abs(amount))
    groups = []
    while len(digits) > 3:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    groups.insert(0, digits)
    return sign + "$" + ",".join(groups)

def wps_pct(val):
    return str(int(round(frappe.utils.flt(val)))) + "%"

def wps_util(plan_row):
    # Live utilization from the budget figures (the stored percentage can be stale).
    approved_amount = frappe.utils.flt(plan_row.total_budget_impact)
    if approved_amount > 0:
        return ((frappe.utils.flt(plan_row.committed_budget) + frappe.utils.flt(plan_row.consumed_budget)) / approved_amount) * 100
    return 0

try:
    wps_plan_rows = {}
    wps_no_plan_rows = []

    wps_jr_names = list({r.job_requisition for r in (doc.get("applicants") or []) if r.job_requisition})
    wps_jr_to_plan = {}
    for wps_jr_name in wps_jr_names:
        wps_jr_to_plan[wps_jr_name] = frappe.db.get_value("Job Requisition", wps_jr_name, "custom_budget_plan")

    for wps_row in (doc.get("applicants") or []):
        wps_plan_name = wps_jr_to_plan.get(wps_row.job_requisition) if wps_row.job_requisition else None
        if not wps_plan_name:
            wps_no_plan_rows.append(wps_row)
            continue
        wps_plan_rows.setdefault(wps_plan_name, []).append(wps_row)

    wps_parts = []

    if not wps_plan_rows and not wps_no_plan_rows:
        wps_parts.append("<p>No applicants in this batch yet -- nothing to summarize.</p>")

    for wps_plan_name, wps_rows_for_plan in wps_plan_rows.items():
        wps_plan = frappe.db.get_value(
            "Workforce Plan", wps_plan_name,
            ["fiscal_year", "department", "workflow_state", "approved_headcount", "approved_budget", "total_budget_impact",
             "committed_headcount", "committed_budget", "consumed_headcount", "consumed_budget",
             "remaining_budget", "remaining_headcount", "custom_budget_utilization_pct",
             "custom_positions_summary"],
            as_dict=True
        )
        if not wps_plan:
            continue

        wps_batch_total = sum(frappe.utils.flt(r.agreed_salary_usd) for r in wps_rows_for_plan)
        wps_batch_names = ", ".join(sorted({r.designation or r.applicant_name or r.job_applicant for r in wps_rows_for_plan}))

        wps_parts.append(
            f"<p><b>Workforce Plan {wps_plan_name}</b> ({wps_plan.department or 'No Department'}, "
            f"FY {wps_plan.fiscal_year or '-'}, status: {wps_plan.workflow_state or '-'})<br>"
            f"Current state -- Total Budget Impact: {wps_money(wps_plan.total_budget_impact)} | "
            f"Committed: {wps_money(wps_plan.committed_budget)} | "
            f"Consumed: {wps_money(wps_plan.consumed_budget)} | "
            f"Remaining: {wps_money(wps_plan.remaining_budget)} | "
            f"Budget Utilization: {wps_pct(wps_util(wps_plan))}<br>"
            f"Headcount -- Approved: {int(frappe.utils.flt(wps_plan.approved_headcount))} | "
            f"Committed: {int(frappe.utils.flt(wps_plan.committed_headcount))} | "
            f"Consumed: {int(frappe.utils.flt(wps_plan.consumed_headcount))} | "
            f"Remaining: {int(frappe.utils.flt(wps_plan.remaining_headcount))} "
            f"({wps_plan.custom_positions_summary or ''})<br>"
            f"This batch's impact -- {len(wps_rows_for_plan)} applicant(s) drawing against this plan "
            f"({wps_batch_names}), totaling {wps_money(wps_batch_total)} in agreed salary.</p>"
        )

    if wps_no_plan_rows:
        wps_no_plan_names = ", ".join(sorted({r.designation or r.applicant_name or r.job_applicant for r in wps_no_plan_rows}))
        wps_parts.append(
            f"<p><b>Not linked to any Workforce Plan</b> -- {len(wps_no_plan_rows)} applicant(s) "
            f"({wps_no_plan_names}) whose Job Requisition has no Recruitment Budget Plan set. "
            f"Their cost is not reflected against any plan's budget/headcount above.</p>"
        )

    doc.workforce_plan_summary = "".join(wps_parts)
except Exception:
    frappe.log_error(frappe.get_traceback(), "CXO Hiring Approval - Workforce Plan Summary")
    frappe.msgprint("The Workforce Plan summary could not be computed: " + frappe.get_traceback().strip().split("\n")[-1], title="Summary Not Computed", indicator="orange")
    doc.workforce_plan_summary = "<p>Could not compute the Workforce Plan summary for this batch. See Error Log for details.</p>"
