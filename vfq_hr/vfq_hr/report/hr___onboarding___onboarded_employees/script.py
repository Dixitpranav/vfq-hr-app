# Report logic for HR - Onboarding - Onboarded Employees (runs like a Frappe non-standard Script Report).

CFG = json.loads("{\"parent\": \"Job Applicant\", \"conf\": \"applicant\", \"date\": \"custom_joining_date\", \"order\": \"custom_joining_date desc\", \"fmap\": {\"company\": \"custom_company\", \"department\": \"custom_department\", \"function\": \"custom_function\"}, \"extra\": [[\"custom_employee\", \"is\", \"set\"]], \"pextra\": [\"job_title\"], \"cols\": [{\"src\": \"p\", \"fn\": \"custom_employee\", \"label\": \"Employee\", \"ft\": \"Link\", \"w\": 150, \"opt\": \"Employee\"}, {\"src\": \"x\", \"fn\": \"employee_name\", \"label\": \"Employee Name\", \"ft\": \"Data\", \"w\": 170}, {\"src\": \"x\", \"fn\": \"emp_status\", \"label\": \"Employee Status\", \"ft\": \"Data\", \"w\": 110}, {\"src\": \"x\", \"fn\": \"date_of_joining\", \"label\": \"Date of Joining\", \"ft\": \"Date\", \"w\": 110}, {\"src\": \"p\", \"fn\": \"name\", \"label\": \"Job Applicant\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Job Applicant\"}, {\"src\": \"p\", \"fn\": \"custom_role_classification\", \"label\": \"Role Classification\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"p\", \"fn\": \"custom_company\", \"label\": \"Company\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Company\"}, {\"src\": \"p\", \"fn\": \"custom_department\", \"label\": \"Department\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Department\"}, {\"src\": \"p\", \"fn\": \"custom_function\", \"label\": \"Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"p\", \"fn\": \"custom_employment_type\", \"label\": \"Employment Type\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employment Type\"}, {\"src\": \"p\", \"fn\": \"custom_hiring_type\", \"label\": \"Hiring Type\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_agreed_salary\", \"label\": \"Agreed Salary (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"source\", \"label\": \"Source\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Job Applicant Source\"}, {\"src\": \"p\", \"fn\": \"custom_vendor\", \"label\": \"Vendor\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Supplier\"}, {\"src\": \"p\", \"fn\": \"job_title\", \"label\": \"Job Opening\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Job Opening\"}, {\"src\": \"x\", \"fn\": \"job_requisition\", \"label\": \"Job Requisition\", \"ft\": \"Data\", \"w\": 170}, {\"src\": \"p\", \"fn\": \"custom_budget_plan\", \"label\": \"Workforce Plan\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Workforce Plan\"}, {\"src\": \"p\", \"fn\": \"custom_joining_date\", \"label\": \"Planned Joining Date\", \"ft\": \"Datetime\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_onboarded_date\", \"label\": \"Onboarded On\", \"ft\": \"Datetime\", \"w\": 130}]}")
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
emps = [r["p__custom_employee"] for r in out] or ["__none__"]
em = {}
for e in frappe.get_all("Employee", filters={"name": ["in", emps]}, fields=["name", "employee_name", "status", "date_of_joining"]):
    em[e.name] = e
ops = [r["p__job_title"] for r in out if r.get("p__job_title")] or ["__none__"]
om = {}
for o in frappe.get_all("Job Opening", filters={"name": ["in", ops]}, fields=["name", "job_requisition"]):
    om[o.name] = o.job_requisition
for r in out:
    e = em.get(r["p__custom_employee"])
    if e:
        r["x__employee_name"] = e.employee_name
        r["x__emp_status"] = e.status
        r["x__date_of_joining"] = e.date_of_joining
    r["x__job_requisition"] = om.get(r.get("p__job_title"))

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
