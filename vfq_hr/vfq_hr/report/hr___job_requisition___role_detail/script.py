# Report logic for HR - Job Requisition - Role Detail (runs like a Frappe non-standard Script Report).

CFG = json.loads("{\"parent\": \"Job Requisition\", \"child\": \"Job Requisition Role\", \"pfield\": \"custom_roles\", \"conf\": \"self\", \"date\": \"posting_date\", \"state\": \"workflow_state\", \"order\": \"posting_date desc, creation desc\", \"fmap\": {\"company\": \"company\", \"department\": \"department\"}, \"cols\": [{\"src\": \"p\", \"fn\": \"name\", \"label\": \"Job Requisition\", \"ft\": \"Link\", \"w\": 170, \"opt\": \"Job Requisition\"}, {\"src\": \"p\", \"fn\": \"custom_requisition_title\", \"label\": \"Title\", \"ft\": \"Data\", \"w\": 180}, {\"src\": \"p\", \"fn\": \"posting_date\", \"label\": \"Posting Date\", \"ft\": \"Date\", \"w\": 130}, {\"src\": \"p\", \"fn\": \"department\", \"label\": \"Department\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Department\"}, {\"src\": \"p\", \"fn\": \"workflow_state\", \"label\": \"Status\", \"ft\": \"Link\", \"w\": 160, \"opt\": \"Workflow State\"}, {\"src\": \"c\", \"fn\": \"role_code\", \"label\": \"Position Code\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"role_title\", \"label\": \"Role Name (optional)\", \"ft\": \"Data\", \"w\": 180}, {\"src\": \"c\", \"fn\": \"designation\", \"label\": \"Position Title\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"c\", \"fn\": \"role_classification\", \"label\": \"Position Title\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Designation\"}, {\"src\": \"c\", \"fn\": \"custom_function\", \"label\": \"Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"c\", \"fn\": \"custom_sub_function\", \"label\": \"Sub Function\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Function\"}, {\"src\": \"c\", \"fn\": \"no_of_positions\", \"label\": \"Positions\", \"ft\": \"Int\", \"w\": 90}, {\"src\": \"c\", \"fn\": \"role_type\", \"label\": \"Role Type\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"custom_employment_type\", \"label\": \"Employment Type\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employment Type\"}, {\"src\": \"c\", \"fn\": \"hiring_manager\", \"label\": \"Hiring Manager\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employee\"}, {\"src\": \"c\", \"fn\": \"project\", \"label\": \"Project\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Project\"}, {\"src\": \"c\", \"fn\": \"location\", \"label\": \"Country\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Country\"}, {\"src\": \"c\", \"fn\": \"budgeted\", \"label\": \"Budgeted?\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"lower_salary_range\", \"label\": \"Salary Range Low (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"custom_mid_salary_range\", \"label\": \"Salary Range Mid (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"max_salary_range\", \"label\": \"Salary Range Max (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"estimated_cost_usd\", \"label\": \"Estimated Cost (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"per_head_cost_usd\", \"label\": \"Per Head Cost (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"role_being_replaced\", \"label\": \"Employee Being Replaced\", \"ft\": \"Link\", \"w\": 130, \"opt\": \"Employee\"}, {\"src\": \"c\", \"fn\": \"current_cost_type\", \"label\": \"Current Cost Type\", \"ft\": \"Data\", \"w\": 130}, {\"src\": \"c\", \"fn\": \"existing_cost_usd\", \"label\": \"Existing Cost (USD)\", \"ft\": \"Currency\", \"w\": 130}, {\"src\": \"x\", \"fn\": \"cost_impact_usd\", \"label\": \"Replacement Cost Impact (USD)\", \"ft\": \"Currency\", \"w\": 160}]}")
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
    if r.get("c__role_being_replaced") or frappe.utils.flt(r.get("c__existing_cost_usd")):
        r["x__cost_impact_usd"] = frappe.utils.flt(r.get("c__estimated_cost_usd")) - frappe.utils.flt(r.get("c__existing_cost_usd"))

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
