# Server Script: Auto create Job Opening for approved requisitions
# Type: DocType Event | DocType: Job Requisition | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.workflow_state == "Approved":
    for row in (doc.get("custom_roles") or []):
        exists = frappe.db.exists("Job Opening", {"job_requisition": doc.name, "custom_role_code": row.role_code} if row.role_code else {"job_requisition": doc.name, "designation": row.designation})
        if exists:
            continue

        base_title = row.role_classification or row.designation or "Position"
        job_title = base_title

        try:
            job_opening = frappe.get_doc({
                "doctype": "Job Opening",
                "job_title": job_title,
                "planned_vacancies": int(frappe.utils.flt(row.no_of_positions) or 1),
                "vacancies": int(frappe.utils.flt(row.no_of_positions) or 1),
                "designation": row.designation,
                "company": doc.company,
                "job_requisition": doc.name,
                "status": "Open",
                "number_of_positions": row.no_of_positions,
                "department": row.sub_function,
                "custom_function": row.custom_function,
                "custom_sub_function": row.custom_sub_function,
                "custom_role_classification": row.role_classification or row.designation,
                "custom_experience_required": row.experience_required,
                "location": None,
                "custom_country": row.location,
                "custom_role_code": row.role_code,
                "lower_range": row.lower_salary_range,
                "upper_range": row.max_salary_range,
                "currency": "USD",
                "closes_on": doc.get("expected_by"),
                "description": (row.role_description or doc.get("description") or row.expertise_skillset),
                "custom_vendor": row.vendor,
                "custom_confidential_hiring": doc.get("custom_confidential_hiring"),
                "employment_type": row.get("custom_employment_type"),
                "custom_mid_range": row.get("custom_mid_salary_range"),
                "custom_variable_pay_type": row.get("custom_variable_pay_type"),
                "custom_variable_pay_basis": row.get("custom_variable_pay_basis"),
                "custom_variable_pay_value": row.get("custom_variable_pay_value"),
                "custom_budget_line": doc.custom_budget_line,
                "custom_cost_center": doc.custom_cost_center,
                "custom_project": row.project,
                "custom_budget_plan": doc.custom_budget_plan,
                "custom_reports_to": row.hiring_manager,
            })
            job_opening.insert(ignore_permissions=True)
            if not doc.custom_job_opening:
                doc.db_set("custom_job_opening", job_opening.name)
        except Exception as err:
            frappe.log_error(title="Auto Job Opening creation failed", message=str(err))
            frappe.throw(
                "The requisition could not be approved because its Job Opening for " + str(row.designation) + " could not be created: " + str(err),
                title="Job Opening Not Created"
            )
