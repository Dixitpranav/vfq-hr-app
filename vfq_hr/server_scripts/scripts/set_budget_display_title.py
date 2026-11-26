# Server Script: Set Budget Display Title
# Type: DocType Event | DocType: Budget | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

account_names = []
for row in (doc.get("accounts") or []):
    if row.account and row.account not in account_names:
        account_names.append(row.account)

if account_names:
    label = account_names[0]
    if len(account_names) > 1:
        label = label + " +" + str(len(account_names) - 1) + " more"
else:
    label = doc.cost_center or doc.name

if doc.cost_center and account_names:
    label = label + " (" + doc.cost_center + ")"

doc.custom_budget_title = label
