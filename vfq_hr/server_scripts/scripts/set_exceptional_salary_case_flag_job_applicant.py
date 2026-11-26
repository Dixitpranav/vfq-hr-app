# Server Script: Set Exceptional Salary Case Flag (Job Applicant)
# Type: DocType Event | DocType: Job Applicant | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Auto-computes the hidden Exceptional Salary Case flag on Job Applicant.
# Compares the agreed salary against the linked Position's (Job Requisition Role row's)
# max salary range. Runs on every save so the flag is always current before CXO rollup reads it.
# This does not change any existing Job Applicant validation -- it only sets one field.

doc.custom_exceptional_salary_case = 0

if doc.get('custom_position') and doc.get('custom_agreed_salary'):
    prange = frappe.db.get_value('Job Requisition Role', doc.custom_position, ['lower_salary_range', 'max_salary_range'], as_dict=True)
    if prange and prange.max_salary_range:
        if frappe.utils.flt(doc.custom_agreed_salary) > frappe.utils.flt(prange.max_salary_range):
            doc.custom_exceptional_salary_case = 1
