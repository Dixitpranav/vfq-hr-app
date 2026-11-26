# Server Script: Consume Budget Automatically
# Type: DocType Event | DocType: Job Applicant | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if (
    doc.custom_recruitment_status == "Onboarded"
    and not doc.get("custom_budget_consumed")
):
    headcount_increment = 1
    budget_increment = frappe.utils.flt(doc.custom_agreed_salary)

    job_requisition_name = None
    if doc.job_title:
        job_requisition_name = frappe.db.get_value("Job Opening", doc.job_title, "job_requisition")

    job_req = frappe.get_doc("Job Requisition", job_requisition_name) if job_requisition_name else None

    # Per-head estimate this hire was originally committed at, so we release
    # exactly that share of the plan's committed budget (not the whole requisition).
    committed_release_headcount = 0
    committed_release_budget = 0
    if job_req and frappe.utils.flt(job_req.no_of_positions) > 0:
        committed_release_headcount = headcount_increment
        committed_release_budget = frappe.utils.flt(job_req.custom_annual_budget_impact) / frappe.utils.flt(job_req.no_of_positions)

    if doc.custom_budget_plan:
        budget_plan = frappe.get_doc("Workforce Plan", doc.custom_budget_plan)

        if budget_plan.docstatus != 1:
            frappe.throw(
                f"{doc.applicant_name or doc.name} cannot be marked Onboarded against Workforce Plan "
                f"{budget_plan.name}, because that plan has not been submitted/approved yet "
                f"(currently \"{budget_plan.workflow_state or 'Draft'}\"). Budget and headcount can only be "
                f"consumed against a fully approved Workforce Plan -- get it through its approval workflow "
                f"first, or point this applicant's requisition to a different, already-approved plan.",
                title="Workforce Plan Not Approved"
            )

        new_plan_consumed_headcount = frappe.utils.flt(budget_plan.consumed_headcount) + headcount_increment
        new_plan_consumed_budget = frappe.utils.flt(budget_plan.consumed_budget) + budget_increment

        new_plan_committed_headcount = max(
            frappe.utils.flt(budget_plan.committed_headcount) - committed_release_headcount, 0
        )
        new_plan_committed_budget = max(
            frappe.utils.flt(budget_plan.committed_budget) - committed_release_budget, 0
        )

        budget_plan.db_set("consumed_headcount", new_plan_consumed_headcount)
        budget_plan.db_set("consumed_budget", new_plan_consumed_budget)
        budget_plan.db_set("committed_headcount", new_plan_committed_headcount)
        budget_plan.db_set("committed_budget", new_plan_committed_budget)
        budget_plan.db_set(
            "remaining_headcount",
            frappe.utils.flt(budget_plan.approved_headcount)
            - new_plan_committed_headcount
            - new_plan_consumed_headcount,
        )
        budget_plan.db_set(
            "remaining_budget",
            frappe.utils.flt(budget_plan.total_budget_impact)
            - new_plan_committed_budget
            - new_plan_consumed_budget,
        )

        # Keep the plan's summary fields in step with the counters above
        # (db_set does not run the plan's before-save summary script).
        plan_approved_hc = frappe.utils.flt(budget_plan.approved_headcount)
        plan_approved_budget = frappe.utils.flt(budget_plan.total_budget_impact)
        plan_open_hc = max(plan_approved_hc - new_plan_committed_headcount - new_plan_consumed_headcount, 0)
        if plan_approved_hc > 0:
            budget_plan.db_set("custom_headcount_utilization_pct", ((new_plan_committed_headcount + new_plan_consumed_headcount) / plan_approved_hc) * 100)
        if plan_approved_budget > 0:
            budget_plan.db_set("custom_budget_utilization_pct", ((new_plan_committed_budget + new_plan_consumed_budget) / plan_approved_budget) * 100)
        plan_summary_text = str(int(new_plan_consumed_headcount)) + " filled / " + str(int(plan_open_hc)) + " open / " + str(int(plan_approved_hc)) + " approved"
        budget_plan.db_set("custom_positions_summary", plan_summary_text)

    if job_req:
        new_consumed_headcount = frappe.utils.flt(job_req.custom_consumed_headcount) + headcount_increment
        new_consumed_budget = frappe.utils.flt(job_req.custom_consumed_budget) + budget_increment
        job_req.db_set("custom_consumed_headcount", new_consumed_headcount)
        job_req.db_set("custom_consumed_budget", new_consumed_budget)
        job_req.db_set(
            "custom_remaining_headcount",
            frappe.utils.flt(job_req.custom_approved_headcount) - new_consumed_headcount,
        )
        job_req.db_set(
            "custom_remaining_budget",
            frappe.utils.flt(job_req.custom_approved_budget) - new_consumed_budget,
        )

    doc.db_set("custom_budget_consumed", 1)
