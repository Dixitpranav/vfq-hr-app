# Server Script: Refresh APR Rollup on Probation Review Submit
# Type: DocType Event | DocType: Probation Review | Event: After Submit
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.employee:
    apr_names = frappe.get_all("Annual Performance Review", filters={"employee": doc.employee}, pluck="name")
    for apr_name in apr_names:
        apr = frappe.get_doc("Annual Performance Review", apr_name)
        apr.save(ignore_permissions=True)
