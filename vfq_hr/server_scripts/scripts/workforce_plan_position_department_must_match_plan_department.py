# Server Script: Workforce Plan - Position Department Must Match Plan Department
# Type: DocType Event | DocType: Workforce Plan | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Keeps Workforce Plan Position rows consistent with the plan's own Department,
# for reporting: each row's Department (sub_function) must be the plan-level
# Department itself or one of its sub-departments in the Department tree.
# This is the server-side guarantee behind the client-side dropdown filter in
# 'Workforce Plan - Function Tree Filters' -- enforced here too so a direct API
# insert/update (which skips the Desk form's query filter) can't create a
# mismatched row.

if doc.department:
    valid_departments = set(
        d.name for d in frappe.get_list(
            'Department',
            filters=[['name', 'descendants of (inclusive)', doc.department]]
        )
    )
    for row in (doc.positions or []):
        if row.sub_function and row.sub_function not in valid_departments:
            frappe.throw(
                'Row #' + str(row.idx) + ': Department "' + row.sub_function + '" is not the plan\'s Department ("'
                + doc.department + '") or one of its sub-departments. Pick a Department within "' + doc.department
                + '" for this row, or change the plan Department above.'
            )
