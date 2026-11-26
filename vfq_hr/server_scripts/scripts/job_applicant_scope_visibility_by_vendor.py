# Server Script: Job Applicant - Scope Visibility by Vendor
# Type: Permission Query | DocType: Job Applicant
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

has_vendor_role = frappe.db.exists("Has Role", {"parent": user, "role": "Job Opening Vendor", "parenttype": "User"})
is_sys_manager = frappe.db.exists("Has Role", {"parent": user, "role": "System Manager", "parenttype": "User"})

if has_vendor_role and not is_sys_manager:
    supplier_names = frappe.db.sql_list("""
        select distinct su.name
        from `tabSupplier` su
        inner join `tabPortal User` pu on pu.parent = su.name and pu.parenttype = 'Supplier'
        where pu.user = %s
    """, (user,))
    if supplier_names:
        suppliers_quoted = ", ".join(frappe.db.escape(s) for s in supplier_names)
        conditions = "`tabJob Applicant`.custom_vendor in ({0})".format(suppliers_quoted)
    else:
        conditions = "1=0"
