# Report logic for HR - Workforce Plan - Position Detail (runs like a Frappe non-standard Script Report).

CFG = json.loads("{\"parent\": \"Workforce Plan\", \"child\": \"Workforce Plan Position\", \"pfield\": \"positions\", \"conf\": \"self\", \"date\": \"creation\", \"state\": \"workflow_state\", \"fmap\": {\"company\": \"custom_company\", \"department\": \"department\", \"function\": \"custom_function\", \"fiscal_year\": \"fiscal_year\"}, \"cols\": [{\"src\": \"p\", \"fn\": \"name\", \"label\": \"Workforce Plan\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Workforce Plan\"}, {\"src\": \"p\", \"fn\": \"fiscal_year\", \"label\": \"Fiscal Year\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Fiscal Year\"}, {\"src\": \"p\", \"fn\": \"custom_company\", \"label\": \"Company\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Company\"}, {\"src\": \"p\", \"fn\": \"department\", \"label\": \"Department\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Department\"}, {\"src\": \"p\", \"fn\": \"workflow_state\", \"label\": \"Plan Status\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Workflow State\"}, {\"src\": \"p\", \"fn\": \"custom_confidential_hiring\", \"label\": \"Confidential\", \"ft\": \"Check\", \"w\": 90}, {\"src\": \"c\", \"fn\": \"role_code\", \"label\": \"Position Code\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"position\", \"label\": \"Position\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"c\", \"fn\": \"role_classification\", \"label\": \"Position Title\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"c\", \"fn\": \"function\", \"label\": \"Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"c\", \"fn\": \"custom_sub_function\", \"label\": \"Sub Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"c\", \"fn\": \"custom_employment_type\", \"label\": \"Employment Type\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employment Type\"}, {\"src\": \"c\", \"fn\": \"role_type\", \"label\": \"New/Existing Role\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"role_count\", \"label\": \"Role Count\", \"ft\": \"Int\", \"w\": 90}, {\"src\": \"c\", \"fn\": \"existing_cost_usd\", \"label\": \"Existing Cost (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"current_entity_status\", \"label\": \"Current Entity Status\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"hiring_manager\", \"label\": \"Hiring Manager\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employee\"}, {\"src\": \"c\", \"fn\": \"hiring_manager_name\", \"label\": \"Hiring Manager Name\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"experience_required\", \"label\": \"Experience Required\", \"ft\": \"Data\", \"w\": 130}]}")
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
