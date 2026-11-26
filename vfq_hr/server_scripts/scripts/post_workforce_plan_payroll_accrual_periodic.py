# Server Script: Post Workforce Plan Payroll Accrual (Periodic)
# Type: Scheduler Event | Frequency: Monthly
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

plans = frappe.get_all(
    "Workforce Plan",
    fields=["name", "budget_line", "cost_center", "consumed_budget", "custom_last_posted_consumed_budget"]
)

by_company = {}
skipped = []

for p in plans:
    consumed = frappe.utils.flt(p.consumed_budget)
    last_posted = frappe.utils.flt(p.custom_last_posted_consumed_budget)
    delta_usd = consumed - last_posted
    if delta_usd <= 0:
        continue
    if not p.budget_line or not p.cost_center:
        skipped.append({"plan": p.name, "reason": "missing budget_line or cost_center"})
        continue

    company = frappe.db.get_value("Cost Center", p.cost_center, "company")
    if not company:
        skipped.append({"plan": p.name, "reason": "could not resolve company from cost_center '%s'" % p.cost_center})
        continue

    budget_accounts = frappe.get_all(
        "Budget Account",
        filters={"parent": p.budget_line, "parenttype": "Budget"},
        fields=["account"]
    )
    if not budget_accounts:
        skipped.append({"plan": p.name, "reason": "Budget '%s' has no accounts configured" % p.budget_line})
        continue
    account = budget_accounts[0].account
    is_group = frappe.db.get_value("Account", account, "is_group")
    if is_group:
        skipped.append({"plan": p.name, "reason": "account '%s' on Budget '%s' is a group account and cannot receive a posting" % (account, p.budget_line)})
        continue

    by_company.setdefault(company, []).append({
        "plan": p.name,
        "account": account,
        "cost_center": p.cost_center,
        "delta_usd": delta_usd,
        "consumed": consumed
    })

for company, rows in by_company.items():
    company_currency = frappe.db.get_value("Company", company, "default_currency") or "USD"

    if company_currency == "USD":
        rate = 1.0
    else:
        rate = frappe.db.get_value(
            "Currency Exchange",
            {"from_currency": "USD", "to_currency": company_currency},
            "exchange_rate",
            order_by="date desc"
        )
        if not rate:
            for row in rows:
                skipped.append({"plan": row["plan"], "reason": "no USD -> %s exchange rate found" % company_currency})
            continue

    company_abbr = frappe.db.get_value("Company", company, "abbr")
    credit_account = frappe.db.get_value("Account", "Payroll Payable - " + company_abbr)
    credit_cost_center = frappe.db.get_value("Cost Center", "Main - " + company_abbr)
    if not credit_account or not credit_cost_center:
        for row in rows:
            skipped.append({"plan": row["plan"], "reason": "could not resolve Payroll Payable account / Main cost center for company '%s'" % company})
        continue

    debit_lines = []
    posted_plans = []
    total_in_company_currency = 0.0

    for row in rows:
        amount = frappe.utils.flt(row["delta_usd"] * rate, 2)
        debit_lines.append({
            "account": row["account"],
            "cost_center": row["cost_center"],
            "debit_in_account_currency": amount,
            "credit_in_account_currency": 0,
            "user_remark": "Workforce Plan %s - Consumed budget accrual (USD %.2f x %.4f)" % (row["plan"], row["delta_usd"], rate)
        })
        total_in_company_currency += amount
        posted_plans.append({"plan": row["plan"], "consumed": row["consumed"]})

    if debit_lines:
        debit_lines.append({
            "account": credit_account,
            "cost_center": credit_cost_center,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": frappe.utils.flt(total_in_company_currency, 2),
            "user_remark": "Workforce Plan payroll accrual - periodic (credit)"
        })
        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Journal Entry"
        je.entry_type = "Journal Entry"
        je.company = company
        je.posting_date = frappe.utils.nowdate()
        je.user_remark = "Automated Workforce Plan payroll accrual. USD -> %s rate used: %s. Plans covered: %s" % (
            company_currency, rate, ", ".join([x["plan"] for x in posted_plans])
        )
        for line in debit_lines:
            je.append("accounts", line)
        je.insert(ignore_permissions=True)
        for row in posted_plans:
            frappe.db.set_value("Workforce Plan", row["plan"], "custom_last_posted_consumed_budget", row["consumed"])
        frappe.db.commit()

for row in skipped:
    try:
        frappe.get_doc("Workforce Plan", row["plan"]).add_comment("Comment", "Payroll accrual run skipped this plan: %s" % row["reason"])
    except Exception:
        pass
