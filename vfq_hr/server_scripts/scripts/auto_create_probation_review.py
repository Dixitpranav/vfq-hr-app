# Server Script: Auto Create Probation Review
# Type: DocType Event | DocType: Employee | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if (
    doc.custom_probation_months
    and doc.custom_probation_end_date
):

    existing_review = frappe.db.exists(
        "Probation Review",
        {
            "employee": doc.name
        }
    )

    if not existing_review:

        probation_review = frappe.get_doc({
            "doctype": "Probation Review",

            "employee": doc.name,
            "employee_name": doc.employee_name,

            "department": doc.department,
            "designation": doc.designation,

            "reviewer": doc.reports_to,

            "date_of_joining": doc.date_of_joining,
            "probation_end_date": doc.custom_probation_end_date,

            "auto_created": 1
        })

        probation_review.insert(
            ignore_permissions=True
        )

        frappe.db.set_value(
            "Employee",
            doc.name,
            "custom_confirmation_status",
            "Probation"
        )
