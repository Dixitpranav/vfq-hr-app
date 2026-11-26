# Report logic for HR - Job Applicant - Register (runs like a Frappe non-standard Script Report).

CFG = json.loads("{\"parent\": \"Job Applicant\", \"conf\": \"applicant\", \"date\": \"custom_cv_received_date\", \"state\": \"custom_recruitment_status\", \"order\": \"creation desc\", \"fmap\": {\"company\": \"custom_company\", \"department\": \"custom_department\", \"function\": \"custom_function\"}, \"cols\": [{\"src\": \"p\", \"fn\": \"name\", \"label\": \"Job Applicant\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Job Applicant\"}, {\"src\": \"p\", \"fn\": \"applicant_name\", \"label\": \"First Name\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_last_name\", \"label\": \"Last Name\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"email_id\", \"label\": \"Email Address\", \"ft\": \"Data\", \"w\": 180}, {\"src\": \"p\", \"fn\": \"phone_number\", \"label\": \"Phone Number\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"job_title\", \"label\": \"Job Opening\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Job Opening\"}, {\"src\": \"p\", \"fn\": \"custom_role_classification\", \"label\": \"Role Classification\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"p\", \"fn\": \"custom_role_code\", \"label\": \"Role Code\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_company\", \"label\": \"Company\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Company\"}, {\"src\": \"p\", \"fn\": \"custom_department\", \"label\": \"Department\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Department\"}, {\"src\": \"p\", \"fn\": \"custom_function\", \"label\": \"Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"p\", \"fn\": \"custom_sub_function\", \"label\": \"Sub Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"p\", \"fn\": \"custom_project\", \"label\": \"Project\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Project\"}, {\"src\": \"p\", \"fn\": \"custom_hiring_manager\", \"label\": \"Hiring Manager\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employee\"}, {\"src\": \"p\", \"fn\": \"custom_employment_type\", \"label\": \"Employment Type\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employment Type\"}, {\"src\": \"p\", \"fn\": \"custom_hiring_type\", \"label\": \"Hiring Type\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"source\", \"label\": \"Source\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Job Applicant Source\"}, {\"src\": \"p\", \"fn\": \"custom_vendor\", \"label\": \"Vendor\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Supplier\"}, {\"src\": \"p\", \"fn\": \"custom_current_company\", \"label\": \"Current Company\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_current_notice_period\", \"label\": \"Notice Period\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_cv_received_date\", \"label\": \"CV Received\", \"ft\": \"Datetime\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_ageing_days\", \"label\": \"Ageing (Days)\", \"ft\": \"Int\", \"w\": 100}, {\"src\": \"p\", \"fn\": \"custom_recruitment_status\", \"label\": \"Recruitment Status\", \"ft\": \"Link\", \"w\": 160, \"opt\": \"Workflow State\"}, {\"src\": \"p\", \"fn\": \"custom_cxo_approval_status\", \"label\": \"CXO Approval Status\", \"ft\": \"Data\", \"w\": 150}, {\"src\": \"p\", \"fn\": \"custom_expected_salary\", \"label\": \"Expected Salary (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_agreed_salary\", \"label\": \"Agreed Salary (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_joining_date\", \"label\": \"Joining Date\", \"ft\": \"Datetime\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"custom_employee\", \"label\": \"Employee\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employee\"}]}")
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
