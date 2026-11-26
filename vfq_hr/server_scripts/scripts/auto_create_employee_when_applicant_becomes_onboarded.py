# Server Script: Auto Create Employee when Applicant becomes Onboarded
# Type: DocType Event | DocType: Job Applicant | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if (
    doc.custom_recruitment_status == "Onboarded"
    and not doc.custom_employee_created
):

    cxo_approval_name = frappe.db.get_value("CXO Hiring Approval Applicant", {"job_applicant": doc.name, "parenttype": "CXO Hiring Approval"}, "parent")

    employee = frappe.get_doc({
        "doctype": "Employee",

        "first_name": doc.applicant_name,
        "middle_name": doc.custom_middle_name,
        "last_name": doc.custom_last_name,
        "custom_project": doc.custom_project,
        "custom_vendor": doc.custom_vendor,

        "personal_email": doc.email_id,

        "gender": doc.custom_gender,
        "date_of_birth": doc.custom_date_of_birth,
        "marital_status": doc.custom_marital_status,

        "designation": doc.designation,
        "department": doc.custom_department,
        "custom_role_classification": doc.custom_role_classification,
        "custom_hiring_type": doc.custom_hiring_type,
        "custom_function": doc.custom_function,
        "custom_sub_function": doc.custom_sub_function,
        "company": doc.custom_company,

        "reports_to": doc.custom_reports_to,
        "branch": doc.custom_branch,
        "payroll_cost_center": doc.custom_cost_center,
        "job_applicant": doc.name,
        "custom_cxo_approval": cxo_approval_name,
        "custom_compa_ratio": doc.get("custom_compa_ratio"),
        "employment_type": doc.get("custom_employment_type"),
        "custom_variable_pay_type": doc.get("custom_variable_pay_type"),
        "custom_variable_pay_basis": doc.get("custom_variable_pay_basis"),
        "custom_variable_pay_value": doc.get("custom_variable_pay_value"),

        "date_of_joining": frappe.utils.getdate(doc.custom_joining_date) if doc.custom_joining_date else None,

        "employment_type": doc.custom_employment_type,

        "custom_budget_plan": doc.custom_budget_plan,
        "custom_budget_line": doc.custom_budget_line,
        "custom_work_country": doc.custom_job_country,

        "custom_agreed_salary": doc.custom_agreed_salary,
        "ctc": doc.custom_agreed_salary,

        "custom_custom_passport_number":
            doc.get("custom_passport_number"),

        "custom_passport_image":
            doc.custom_passport_image
    })

    employee.insert(ignore_permissions=True)

    # Record this employee on the Workforce Plan, Job Requisition and Job Opening so they show
    # under Connections on the Employee record.
    onboarded_parents = [
        ["Workforce Plan", doc.custom_budget_plan],
        ["Job Requisition", frappe.db.get_value("Job Opening", doc.job_title, "job_requisition") if doc.job_title else None],
        ["Job Opening", doc.job_title],
    ]
    for parent_dt, parent_name in onboarded_parents:
        if parent_name and frappe.db.exists(parent_dt, parent_name):
            if not frappe.db.exists("Hiring Flow Employee", {"parent": parent_name, "parenttype": parent_dt, "employee": employee.name}):
                frappe.get_doc({
                    "doctype": "Hiring Flow Employee",
                    "parent": parent_name,
                    "parenttype": parent_dt,
                    "parentfield": "custom_onboarded_employees",
                    "employee": employee.name,
                }).insert(ignore_permissions=True)

    doc.db_set("custom_employee", employee.name)
    doc.db_set("custom_employee_created", 1)
    doc.db_set("custom_onboarded", 1)

    if doc.custom_vendor:
        vendor_probation_months = frappe.db.get_value(
            "Supplier", doc.custom_vendor, "custom_probation_period_months"
        )
        if vendor_probation_months:
            employee.db_set("custom_probation_months", vendor_probation_months)
            if employee.date_of_joining:
                employee.db_set(
                    "custom_probation_end_date",
                    frappe.utils.add_months(employee.date_of_joining, vendor_probation_months),
                )

            # db_set() above does not re-trigger After Save hooks, so force a real
            # resave here to let the existing "Auto Create Probation Review" script
            # (Employee, After Save) fire naturally now that probation fields are set.
            employee.reload()
            employee.save(ignore_permissions=True)
