# Report logic for HR - Workforce Plan - Register (runs like a Frappe non-standard Script Report).

CFG = json.loads("{\"parent\": \"Workforce Plan\", \"conf\": \"self\", \"date\": \"creation\", \"state\": \"workflow_state\", \"fmap\": {\"company\": \"custom_company\", \"department\": \"department\", \"function\": \"custom_function\", \"fiscal_year\": \"fiscal_year\"}, \"cols\": [{\"src\": \"p\", \"fn\": \"name\", \"label\": \"Workforce Plan\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Workforce Plan\"}, {\"src\": \"p\", \"fn\": \"fiscal_year\", \"label\": \"Fiscal Year\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Fiscal Year\"}, {\"src\": \"p\", \"fn\": \"custom_company\", \"label\": \"Company\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Company\"}, {\"src\": \"p\", \"fn\": \"department\", \"label\": \"Department\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Department\"}, {\"src\": \"p\", \"fn\": \"custom_function\", \"label\": \"Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"p\", \"fn\": \"custom_sub_function\", \"label\": \"Sub Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"p\", \"fn\": \"cost_center\", \"label\": \"Cost Center\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Cost Center\"}, {\"src\": \"p\", \"fn\": \"budget_line\", \"label\": \"Budget Line\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Budget\"}, {\"src\": \"p\", \"fn\": \"custom_project\", \"label\": \"Project\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Project\"}, {\"src\": \"p\", \"fn\": \"custom_confidential_hiring\", \"label\": \"Confidential\", \"ft\": \"Check\", \"w\": 90}, {\"src\": \"p\", \"fn\": \"workflow_state\", \"label\": \"Status\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Workflow State\"}, {\"src\": \"p\", \"fn\": \"approved_headcount\", \"label\": \"Approved HC\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"approved_budget\", \"label\": \"Approved Budget (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_monthly_budget_per_headcount\", \"label\": \"Monthly Budget / HC (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"total_budget_impact\", \"label\": \"Total Budget Impact (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"committed_headcount\", \"label\": \"Committed HC\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"committed_budget\", \"label\": \"Committed Budget (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"consumed_headcount\", \"label\": \"Consumed HC\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"consumed_budget\", \"label\": \"Consumed Budget (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"remaining_headcount\", \"label\": \"Remaining HC\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"remaining_budget\", \"label\": \"Remaining Budget (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_headcount_utilization_pct\", \"label\": \"HC Utilisation %\", \"ft\": \"Percent\", \"w\": 110}, {\"src\": \"p\", \"fn\": \"custom_budget_utilization_pct\", \"label\": \"Budget Utilisation %\", \"ft\": \"Percent\", \"w\": 110}, {\"src\": \"p\", \"fn\": \"owner\", \"label\": \"Created By\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"User\"}, {\"src\": \"p\", \"fn\": \"creation\", \"label\": \"Created On\", \"ft\": \"Datetime\", \"w\": 130}]}")
f = filters or {}
P = CFG["parent"]
CONF_ROLES = ["HR Manager", "CHRO", "CAO", "CEO / Final Approver", "System Manager"]
my_roles = frappe.get_all("Has Role", filters={"parent": frappe.session.user, "parenttype": "User"}, pluck="role")
can_conf = frappe.session.user == "Administrator" or len(set(my_roles) & set(CONF_ROLES)) > 0
NONE = ["__none__"]

def conf_set(mode, dt):
    if mode == "self":
        return set(frappe.get_all(dt, filters={"custom_confidential_hiring": 1}, pluck="name"))
    if mode not in ("applicant", "cxo"):
        return set()
    jo = frappe.get_all("Job Opening", filters={"custom_confidential_hiring": 1}, pluck="name") or ["__none__"]
    ja = frappe.get_all("Job Applicant", filters={"job_title": ["in", jo]}, pluck="name") or ["__none__"]
    if mode == "applicant":
        return set(ja)
    return set(frappe.get_all("CXO Hiring Approval Applicant", filters={"job_applicant": ["in", ja], "parenttype": "CXO Hiring Approval"}, pluck="parent"))

try:
    base = set(frappe.get_list(P, pluck="name", limit_page_length=0))
except Exception:
    base = set()
cs = conf_set(CFG.get("conf"), P)
names = (base | cs) if can_conf else (base - cs)

pf = [["name", "in", list(names) or NONE]] + CFG.get("extra", [])
for key in CFG.get("fmap", {}):
    if f.get(key):
        pf.append([CFG["fmap"][key], "=", f.get(key)])
if f.get("from_date") and CFG.get("date"):
    pf.append([CFG["date"], ">=", f.get("from_date")])
if f.get("to_date") and CFG.get("date"):
    pf.append([CFG["date"], "<=", f.get("to_date")])
if f.get("state") and CFG.get("state"):
    pf.append([CFG["state"], "=", f.get("state")])

pcols = [c for c in CFG["cols"] if c["src"] == "p"]
ccols = [c for c in CFG["cols"] if c["src"] == "c"]
pfl = list(set(["name"] + [c["fn"] for c in pcols] + CFG.get("pextra", [])))
prows = frappe.get_all(P, filters=pf, fields=pfl, order_by=CFG.get("order", "creation desc"), limit_page_length=0)
out = []
if CFG.get("child"):
    pmap = {}
    order = {}
    i = 0
    for r in prows:
        pmap[r.name] = r
        order[r.name] = i
        i += 1
    crows = frappe.get_all(CFG["child"], filters={"parent": ["in", list(pmap.keys()) or NONE], "parenttype": P, "parentfield": CFG["pfield"]}, fields=list(set(["parent", "idx"] + [c["fn"] for c in ccols] + CFG.get("cextra", []))), limit_page_length=0)
    crows = sorted(crows, key=lambda x: (order.get(x.parent, 0), x.idx))
    for cr in crows:
        pr = pmap.get(cr.parent)
        row = {"_cur": "USD", "_p": pr, "_c": cr}
        for c in pcols:
            row["p__" + c["fn"]] = pr.get(c["fn"])
        for c in ccols:
            row["c__" + c["fn"]] = cr.get(c["fn"])
        out.append(row)
else:
    for pr in prows:
        row = {"_cur": "USD", "_p": pr}
        for c in pcols:
            row["p__" + c["fn"]] = pr.get(c["fn"])
        out.append(row)

for r in out:
    r.pop("_p", None)
    r.pop("_c", None)
columns = []
for c in CFG["cols"]:
    col = {"fieldname": c["src"] + "__" + c["fn"], "label": c["label"], "fieldtype": c["ft"], "width": c.get("w", 130)}
    if c.get("opt"):
        col["options"] = c["opt"]
    if c["ft"] == "Currency":
        col["options"] = "_cur"
    columns.append(col)
data = columns, out
