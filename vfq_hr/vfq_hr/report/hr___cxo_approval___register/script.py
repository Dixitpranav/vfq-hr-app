# Report logic for HR - CXO Approval - Register (runs like a Frappe non-standard Script Report).

CFG = json.loads("{\"parent\": \"CXO Hiring Approval\", \"child\": \"CXO Hiring Approval Applicant\", \"pfield\": \"applicants\", \"conf\": \"cxo\", \"date\": \"creation\", \"state\": \"workflow_state\", \"fmap\": {\"company\": \"company\"}, \"cols\": [{\"src\": \"p\", \"fn\": \"name\", \"label\": \"CXO Hiring Approval\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"CXO Hiring Approval\"}, {\"src\": \"p\", \"fn\": \"title\", \"label\": \"Batch Title\", \"ft\": \"Data\", \"w\": 180}, {\"src\": \"p\", \"fn\": \"company\", \"label\": \"Company\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Company\"}, {\"src\": \"p\", \"fn\": \"workflow_state\", \"label\": \"Status\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Workflow State\"}, {\"src\": \"p\", \"fn\": \"creation\", \"label\": \"Created On\", \"ft\": \"Datetime\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"job_applicant\", \"label\": \"Job Applicant\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Job Applicant\"}, {\"src\": \"c\", \"fn\": \"applicant_name\", \"label\": \"Applicant Name\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"custom_position_title\", \"label\": \"Position Title\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"c\", \"fn\": \"designation\", \"label\": \"Designation\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"c\", \"fn\": \"custom_employment_type\", \"label\": \"Employment Type\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employment Type\"}, {\"src\": \"c\", \"fn\": \"function\", \"label\": \"Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"c\", \"fn\": \"custom_sub_function\", \"label\": \"Sub Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"c\", \"fn\": \"department\", \"label\": \"Department\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Department\"}, {\"src\": \"c\", \"fn\": \"project\", \"label\": \"Project\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Project\"}, {\"src\": \"c\", \"fn\": \"job_requisition\", \"label\": \"Job Requisition\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Job Requisition\"}, {\"src\": \"c\", \"fn\": \"vendor\", \"label\": \"Vendor\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Supplier\"}, {\"src\": \"x\", \"fn\": \"approval_type\", \"label\": \"Approval Type\", \"ft\": \"Data\", \"w\": 110}, {\"src\": \"x\", \"fn\": \"recommended_salary_range\", \"label\": \"Recommended Salary Range\", \"ft\": \"Data\", \"w\": 170}, {\"src\": \"c\", \"fn\": \"agreed_salary_usd\", \"label\": \"Agreed Salary (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"custom_agreed_salary_monthly\", \"label\": \"Agreed Salary Monthly (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"agreed_salary_qar\", \"label\": \"Agreed Salary (QAR)\", \"ft\": \"Float\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"custom_variable_pay_type\", \"label\": \"Variable Pay Type\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"custom_variable_pay_value\", \"label\": \"Variable Pay Value\", \"ft\": \"Float\", \"w\": 130}, {\"src\": \"x\", \"fn\": \"hr_comments\", \"label\": \"HR Comments\", \"ft\": \"Data\", \"w\": 220}], \"cextra\": [\"position\"]}")
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
pn = list(set([r.get("_c").parent for r in out])) or ["__none__"]
appr = {}
for a in frappe.get_all("CXO Standard Approval", filters={"parent": ["in", pn]}, fields=["parent", "position", "recommended_salary_range", "hr_comments"]):
    appr[(a.parent, a.position)] = ["Standard", a.recommended_salary_range, a.hr_comments]
for a in frappe.get_all("CXO Exceptional Approval", filters={"parent": ["in", pn]}, fields=["parent", "position", "recommended_salary_range", "hr_comments"]):
    appr[(a.parent, a.position)] = ["Exceptional", a.recommended_salary_range, a.hr_comments]
for r in out:
    m = appr.get((r.get("_c").parent, r.get("_c").position))
    if m:
        r["x__approval_type"] = m[0]
        r["x__recommended_salary_range"] = m[1]
        r["x__hr_comments"] = m[2]

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
