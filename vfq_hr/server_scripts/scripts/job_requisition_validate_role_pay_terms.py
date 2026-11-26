# Server Script: Job Requisition - Validate Role Pay Terms
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

for role_row in (doc.get("custom_roles") or []):
    where = "role row " + str(role_row.idx)
    lo = frappe.utils.flt(role_row.get("lower_salary_range"))
    hi = frappe.utils.flt(role_row.get("max_salary_range"))
    mid = frappe.utils.flt(role_row.get("custom_mid_salary_range"))
    if mid and lo and mid < lo:
        frappe.throw("Mid Salary Range cannot be below the minimum salary on " + where + ".", title="Salary Range")
    if mid and hi and mid > hi:
        frappe.throw("Mid Salary Range cannot be above the maximum salary on " + where + ".", title="Salary Range")
    vtype = role_row.get("custom_variable_pay_type") or "None"
    if vtype != "None":
        if not role_row.get("custom_variable_pay_basis"):
            frappe.throw("Choose Fixed Amount or % of Salary for the " + vtype + " on " + where + ".", title="Bonus / Commission")
        if frappe.utils.flt(role_row.get("custom_variable_pay_value")) <= 0:
            frappe.throw("Enter a " + vtype + " value greater than zero on " + where + ".", title="Bonus / Commission")
        if role_row.get("custom_variable_pay_basis") == "% of Salary" and frappe.utils.flt(role_row.get("custom_variable_pay_value")) > 100:
            frappe.throw("The " + vtype + " percentage on " + where + " cannot be more than 100.", title="Bonus / Commission")
    if doc.is_new() and not role_row.get("custom_employment_type"):
        frappe.throw("Select an Employment Type on " + where + ".", title="Employment Type")
