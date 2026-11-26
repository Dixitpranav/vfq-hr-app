# Report logic for HR - Job Opening - Register (runs like a Frappe non-standard Script Report).

CFG = json.loads("{\"parent\": \"Job Opening\", \"conf\": \"self\", \"date\": \"posted_on\", \"state\": \"status\", \"order\": \"posted_on desc, creation desc\", \"fmap\": {\"company\": \"company\", \"department\": \"department\", \"function\": \"custom_function\"}, \"cols\": [{\"src\": \"p\", \"fn\": \"name\", \"label\": \"Job Opening\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Job Opening\"}, {\"src\": \"p\", \"fn\": \"job_title\", \"label\": \"Job Title\", \"ft\": \"Data\", \"w\": 180}, {\"src\": \"p\", \"fn\": \"custom_role_classification\", \"label\": \"Role Classification\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"p\", \"fn\": \"custom_role_code\", \"label\": \"Role Code\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"designation\", \"label\": \"Designation\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"p\", \"fn\": \"job_requisition\", \"label\": \"Job Requisition\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Job Requisition\"}, {\"src\": \"p\", \"fn\": \"custom_budget_plan\", \"label\": \"Workforce Plan\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Workforce Plan\"}, {\"src\": \"p\", \"fn\": \"company\", \"label\": \"Company\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Company\"}, {\"src\": \"p\", \"fn\": \"department\", \"label\": \"Department\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Department\"}, {\"src\": \"p\", \"fn\": \"custom_function\", \"label\": \"Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"p\", \"fn\": \"custom_sub_function\", \"label\": \"Sub Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"p\", \"fn\": \"employment_type\", \"label\": \"Employment Type\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employment Type\"}, {\"src\": \"p\", \"fn\": \"location\", \"label\": \"Location\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Branch\"}, {\"src\": \"p\", \"fn\": \"custom_country\", \"label\": \"Country\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Country\"}, {\"src\": \"p\", \"fn\": \"custom_reports_to\", \"label\": \"Reports To\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employee\"}, {\"src\": \"p\", \"fn\": \"status\", \"label\": \"Status\", \"ft\": \"Data\", \"w\": 90}, {\"src\": \"p\", \"fn\": \"posted_on\", \"label\": \"Posted On\", \"ft\": \"Datetime\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"closes_on\", \"label\": \"Closes On\", \"ft\": \"Date\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"closed_on\", \"label\": \"Closed On\", \"ft\": \"Date\", \"w\": 130}, {\"src\": \"x\", \"fn\": \"days_open\", \"label\": \"Days Open\", \"ft\": \"Int\", \"w\": 90}, {\"src\": \"p\", \"fn\": \"planned_vacancies\", \"label\": \"Planned Vacancies\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"vacancies\", \"label\": \"Vacancies\", \"ft\": \"Int\", \"w\": 90}, {\"src\": \"p\", \"fn\": \"lower_range\", \"label\": \"Salary Range Low (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_mid_range\", \"label\": \"Salary Range Mid (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"upper_range\", \"label\": \"Salary Range Max (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_confidential_hiring\", \"label\": \"Confidential\", \"ft\": \"Check\", \"w\": 90}, {\"src\": \"p\", \"fn\": \"custom_closing_sla_days\", \"label\": \"Closing SLA Days\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"custom_sla_breached\", \"label\": \"SLA Breached\", \"ft\": \"Check\", \"w\": 90}]}")
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
    if r.get("p__posted_on"):
        r["x__days_open"] = frappe.utils.date_diff(r.get("p__closed_on") or frappe.utils.nowdate(), r.get("p__posted_on"))

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
