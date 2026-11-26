# Server Script: Validate Budget Line Account (Job Requisition)
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.custom_budget_line:
    budget = vfq_budget_header(doc.custom_budget_line)
    if budget:
        if budget.docstatus != 1:
            frappe.throw(
                "Budget Line \"" + doc.custom_budget_line + "\" is still in Draft and has not been submitted/approved yet. " +
                "Ask an Accounts Manager to submit this Budget before it can be used on a Job Requisition."
            )
        accounts = vfq_budget_accounts(doc.custom_budget_line)
        if not accounts:
            frappe.msgprint(
                "Budget \"" + doc.custom_budget_line + "\" has no accounts configured. Actual spend will never be checked against this requisition until an account is added to that Budget.",
                indicator="orange",
                title="Budget Line Warning",
            )
        else:
            for a in accounts:
                acc = frappe.db.get_value("Account", a.account, ["is_group", "root_type", "report_type"], as_dict=True)
                if acc and acc.is_group:
                    frappe.throw(
                        "Budget \"" + doc.custom_budget_line + "\" points to group/header account \"" + a.account + "\", which can never receive an actual posting."
                    )
                if acc and (acc.root_type != "Expense" or acc.report_type != "Profit and Loss"):
                    frappe.msgprint(
                        "Budget \"" + doc.custom_budget_line + "\" points to account \"" + a.account + "\" classified as " + str(acc.root_type) + " / " + str(acc.report_type) + ", not a Profit and Loss Expense account.",
                        indicator="orange",
                        title="Budget Line Warning",
                    )
