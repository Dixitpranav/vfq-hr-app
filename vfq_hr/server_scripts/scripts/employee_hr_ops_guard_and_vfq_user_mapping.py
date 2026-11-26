# Server Script: Employee - HR Ops Guard and VFQ User Mapping
# Type: DocType Event | DocType: Employee | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

CORE_X = json.loads("[\"company\",\"designation\",\"department\",\"custom_role_classification\",\"custom_hiring_type\",\"custom_function\",\"custom_sub_function\",\"reports_to\",\"branch\",\"payroll_cost_center\",\"job_applicant\",\"custom_cxo_approval\",\"custom_compa_ratio\",\"employment_type\",\"custom_variable_pay_type\",\"custom_variable_pay_basis\",\"custom_variable_pay_value\",\"date_of_joining\",\"custom_budget_plan\",\"custom_budget_line\",\"custom_work_country\",\"custom_agreed_salary\",\"ctc\",\"custom_project\",\"custom_vendor\",\"status\"]")
CORE = CORE_X + ["custom_activation_status"]
NUM = ["Currency", "Float", "Int", "Percent"]
roles = frappe.get_all("Has Role", filters={"parent": frappe.session.user, "parenttype": "User"}, pluck="role")
is_admin = frappe.session.user == "Administrator" or "System Manager" in roles
is_hr_manager = is_admin or "HR Manager" in roles
is_ops = ("HR Ops" in roles) or ("HR Ops - VFQ Email" in roles)
via_activation = doc.flags.get("via_activation")
old = doc.get_doc_before_save()

if old and not via_activation:
    # Activation only through the Activate action
    if old.custom_activation_status == "To be activated" and (doc.status != old.status or doc.custom_activation_status != old.custom_activation_status) and not is_admin:
        frappe.throw("This employee is awaiting activation. Use the <b>Activate</b> button to make the record Active.")
    # HR Ops may fill in missing details but not change core fields
    if is_ops and not is_hr_manager:
        changed = []
        for f in CORE:
            ov = old.get(f)
            nv = doc.get(f)
            df = doc.meta.get_field(f)
            if df and df.fieldtype in NUM:
                same = frappe.utils.flt(ov) == frappe.utils.flt(nv)
                empty = not frappe.utils.flt(ov)
            elif df and df.fieldtype in ["Date", "Datetime"]:
                same = str(frappe.utils.getdate(ov) if ov else "") == str(frappe.utils.getdate(nv) if nv else "")
                empty = not ov
            else:
                same = (ov or "") == (nv or "")
                empty = not ov
            if not same and not empty:
                changed.append(df.label if df else f)
        if changed:
            frappe.throw("HR Ops can update personal details and fill missing fields, but cannot change these core fields: <b>" + ", ".join(changed) + "</b>. Ask an HR Manager if a change is needed.")

# VFQ email entered -> create and link the system user
if doc.company_email and not doc.user_id and doc.status == "Active":
    email = doc.company_email.strip().lower()
    doc.company_email = email
    existing = frappe.db.get_value("User", email, "name")
    if existing:
        other = frappe.db.get_value("Employee", {"user_id": existing, "name": ["!=", doc.name]}, "name")
        if other:
            frappe.throw("The user " + email + " is already linked to employee " + other + ".")
        doc.user_id = existing
    else:
        u = frappe.get_doc({"doctype": "User", "email": email, "first_name": doc.first_name, "middle_name": doc.middle_name, "last_name": doc.last_name, "user_type": "System User", "enabled": 1, "send_welcome_email": 1})
        u.insert(ignore_permissions=True)
        doc.user_id = u.name
        frappe.msgprint("System user " + email + " created and linked to this employee.", alert=True)
