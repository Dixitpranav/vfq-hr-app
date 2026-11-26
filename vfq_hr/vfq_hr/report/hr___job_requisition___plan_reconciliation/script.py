# Report logic for HR - Job Requisition - Plan Reconciliation (runs like a Frappe non-standard Script Report).

f = filters or {}
CONF_ROLES = ["HR Manager", "CHRO", "CAO", "CEO / Final Approver", "System Manager"]
my_roles = frappe.get_all("Has Role", filters={"parent": frappe.session.user, "parenttype": "User"}, pluck="role")
can_conf = frappe.session.user == "Administrator" or len(set(my_roles) & set(CONF_ROLES)) > 0
NONE = ["__none__"]
flt = frappe.utils.flt
cint = frappe.utils.cint
today = frappe.utils.nowdate()
now = frappe.utils.now_datetime()

def visible(dt, mode, can_conf):
    try:
        base = set(frappe.get_list(dt, pluck="name", limit_page_length=0))
    except Exception:
        base = set()
    if mode == "self":
        cs = set(frappe.get_all(dt, filters={"custom_confidential_hiring": 1}, pluck="name"))
    else:
        jo = frappe.get_all("Job Opening", filters={"custom_confidential_hiring": 1}, pluck="name") or ["__none__"]
        ja = frappe.get_all("Job Applicant", filters={"job_title": ["in", jo]}, pluck="name") or ["__none__"]
        cs = set(ja)
        if mode == "cxo":
            cs = set(frappe.get_all("CXO Hiring Approval Applicant", filters={"job_applicant": ["in", ja], "parenttype": "CXO Hiring Approval"}, pluck="parent"))
    if can_conf:
        return base | cs
    return base - cs

def C(fieldname, label, fieldtype="Data", options=None, width=130):
    d = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, "width": width}
    if options:
        d["options"] = options
    if fieldtype == "Currency":
        d["options"] = "_cur"
    return d

def days(a, b):
    if not a or not b:
        return None
    return round(frappe.utils.time_diff_in_hours(b, a) / 24.0, 1)

def history(dt, names, field, docs):
    res = {}
    for n in names:
        res[n] = []
    vs = frappe.get_all("Version", filters={"ref_doctype": dt, "docname": ["in", list(names) or ["__none__"]]}, fields=["docname", "creation", "owner", "data"], order_by="creation asc", limit_page_length=0)
    for v in vs:
        try:
            d = json.loads(v.data or "{}")
        except Exception:
            continue
        for ch in (d.get("changed") or []):
            if ch[0] == field and ch[2] and ch[1] != ch[2]:
                if not res[v.docname]:
                    res[v.docname].append([ch[1] or "Draft", docs[v.docname].creation, docs[v.docname].owner])
                res[v.docname].append([ch[2], v.creation, v.owner])
    for n in names:
        if not res[n]:
            res[n].append([docs[n].get(field) or "Draft", docs[n].creation, docs[n].owner])
    return res

def date_filters(pf, f, datefield):
    if f.get("from_date"):
        pf.append([datefield, ">=", f.get("from_date")])
    if f.get("to_date"):
        pf.append([datefield, "<=", f.get("to_date")])
    return pf
names = visible("Job Requisition", "self", can_conf)
pf = [["name", "in", list(names) or NONE]]
if f.get("company"):
    pf.append(["company", "=", f.get("company")])
if f.get("department"):
    pf.append(["department", "=", f.get("department")])
if f.get("state"):
    pf.append(["workflow_state", "=", f.get("state")])
pf = date_filters(pf, f, "posting_date")
jrs = frappe.get_all("Job Requisition", filters=pf, fields=["name", "custom_requisition_title", "custom_budget_plan", "posting_date", "department", "workflow_state", "no_of_positions", "custom_annual_budget_impact"], order_by="posting_date desc, creation desc", limit_page_length=0)
plans = list(set([j.custom_budget_plan for j in jrs if j.custom_budget_plan])) or NONE
pm = {}
for p in frappe.get_all("Workforce Plan", filters={"name": ["in", plans]}, fields=["name", "workflow_state", "approved_headcount", "approved_budget", "committed_headcount", "committed_budget", "consumed_headcount", "consumed_budget", "remaining_headcount", "remaining_budget"]):
    pm[p.name] = p
pos = {}
for r in frappe.get_all("Job Requisition Role", filters={"parent": ["in", [j.name for j in jrs] or NONE], "parenttype": "Job Requisition"}, fields=["parent", "no_of_positions"]):
    pos[r.parent] = pos.get(r.parent, 0) + cint(r.no_of_positions)
tot_req = {}
tot_bud = {}
for j in frappe.get_all("Job Requisition", filters={"custom_budget_plan": ["in", plans], "workflow_state": ["!=", "Rejected"]}, fields=["name", "custom_budget_plan", "no_of_positions", "custom_annual_budget_impact"]):
    tot_req[j.custom_budget_plan] = tot_req.get(j.custom_budget_plan, 0) + cint(j.no_of_positions)
    tot_bud[j.custom_budget_plan] = tot_bud.get(j.custom_budget_plan, 0) + flt(j.custom_annual_budget_impact)
rows = []
for j in jrs:
    p = pm.get(j.custom_budget_plan) or {}
    req = pos.get(j.name) or cint(j.no_of_positions)
    ahc = cint(p.get("approved_headcount"))
    abud = flt(p.get("approved_budget"))
    rhc = cint(p.get("remaining_headcount"))
    rbud = flt(p.get("remaining_budget"))
    thc = tot_req.get(j.custom_budget_plan, 0)
    tb = tot_bud.get(j.custom_budget_plan, 0)
    flags = []
    if not j.custom_budget_plan:
        flags.append("No Workforce Plan")
    else:
        if thc > ahc:
            flags.append("Headcount over plan")
        if tb > abud:
            flags.append("Budget over plan")
    row = {"_cur": "USD", "jr": j.name, "title": j.custom_requisition_title, "dept": j.department, "state": j.workflow_state, "posting_date": j.posting_date, "plan": j.custom_budget_plan, "plan_state": p.get("workflow_state"),
        "req_hc": req, "req_budget": flt(j.custom_annual_budget_impact), "plan_hc": ahc, "plan_budget": abud, "all_req_hc": thc, "all_req_budget": tb,
        "hc_headroom": ahc - thc, "budget_headroom": abud - tb, "rem_hc": rhc, "rem_budget": rbud,
        "result": ", ".join(flags) if flags else "Within plan"}
    if f.get("exceptions_only") and not flags:
        continue
    rows.append(row)
columns = [C("jr", "Job Requisition", "Link", "Job Requisition", 170), C("title", "Title", "Data", None, 180), C("dept", "Department", "Link", "Department", 150), C("state", "JR Status", "Data", None, 160), C("posting_date", "Posting Date", "Date", None, 100),
    C("plan", "Workforce Plan", "Link", "Workforce Plan", 170), C("plan_state", "Plan Status", "Data", None, 120),
    C("req_hc", "This JR Positions", "Int", None, 110), C("req_budget", "This JR Annual Impact (USD)", "Currency", None, 160),
    C("plan_hc", "Plan Approved HC", "Int", None, 110), C("all_req_hc", "All JRs on Plan - Positions", "Int", None, 150), C("hc_headroom", "HC Headroom", "Int", None, 100),
    C("plan_budget", "Plan Approved Budget (USD)", "Currency", None, 160), C("all_req_budget", "All JRs on Plan - Impact (USD)", "Currency", None, 170), C("budget_headroom", "Budget Headroom (USD)", "Currency", None, 150),
    C("rem_hc", "Plan Remaining HC", "Int", None, 110), C("rem_budget", "Plan Remaining Budget (USD)", "Currency", None, 160), C("result", "Reconciliation Result", "Data", None, 220)]
data = columns, rows
