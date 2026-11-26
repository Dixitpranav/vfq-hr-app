# Report logic for HR - Job Requisition - Register (runs like a Frappe non-standard Script Report).

CFG = json.loads("{\"parent\": \"Job Requisition\", \"conf\": \"self\", \"date\": \"posting_date\", \"state\": \"workflow_state\", \"order\": \"posting_date desc, creation desc\", \"fmap\": {\"company\": \"company\", \"department\": \"department\"}, \"cols\": [{\"src\": \"p\", \"fn\": \"name\", \"label\": \"Job Requisition\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Job Requisition\"}, {\"src\": \"p\", \"fn\": \"custom_requisition_title\", \"label\": \"Title\", \"ft\": \"Data\", \"w\": 200}, {\"src\": \"p\", \"fn\": \"custom_budget_plan\", \"label\": \"Workforce Plan\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Workforce Plan\"}, {\"src\": \"p\", \"fn\": \"posting_date\", \"label\": \"Posting Date\", \"ft\": \"Date\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"company\", \"label\": \"Company\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Company\"}, {\"src\": \"p\", \"fn\": \"department\", \"label\": \"Department\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Department\"}, {\"src\": \"p\", \"fn\": \"requested_by\", \"label\": \"Requested By (HR)\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employee\"}, {\"src\": \"p\", \"fn\": \"requested_by_name\", \"label\": \"Requested By (Name)\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"workflow_state\", \"label\": \"Status\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Workflow State\"}, {\"src\": \"p\", \"fn\": \"expected_by\", \"label\": \"Expected By\", \"ft\": \"Date\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"no_of_positions\", \"label\": \"Positions\", \"ft\": \"Int\", \"w\": 90}, {\"src\": \"p\", \"fn\": \"custom_budget_line\", \"label\": \"Budget Line\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Budget\"}, {\"src\": \"p\", \"fn\": \"custom_cost_center\", \"label\": \"Cost Center\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Cost Center\"}, {\"src\": \"p\", \"fn\": \"custom_approved_headcount\", \"label\": \"Plan Approved HC\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"custom_approved_budget\", \"label\": \"Plan Approved Budget (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_monthly_budget_per_headcount\", \"label\": \"Monthly Budget / HC (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_annual_budget_impact\", \"label\": \"Annual Budget Impact (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_annual_budget_impact_qar\", \"label\": \"Annual Budget Impact (QAR)\", \"ft\": \"Float\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_budget_variance_usd\", \"label\": \"Budget Variance (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_headcount_variance\", \"label\": \"HC Variance\", \"ft\": \"Int\", \"w\": 90}, {\"src\": \"p\", \"fn\": \"custom_remaining_budget\", \"label\": \"Plan Remaining Budget (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_remaining_headcount\", \"label\": \"Plan Remaining HC\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"custom_confidential_hiring\", \"label\": \"Confidential\", \"ft\": \"Check\", \"w\": 90}, {\"src\": \"p\", \"fn\": \"custom_job_opening\", \"label\": \"Job Opening\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Job Opening\"}, {\"src\": \"p\", \"fn\": \"completed_on\", \"label\": \"Completed On\", \"ft\": \"Date\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"time_to_fill\", \"label\": \"Time to Fill\", \"ft\": \"Duration\", \"w\": 130}]}")
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
    byp = {}
    for cr in crows:
        byp.setdefault(cr.parent, []).append(cr)
    ordered = []
    for pr in prows:
        ordered += sorted(byp.get(pr.name, []), key=lambda x: x.idx)
    for cr in ordered:
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
