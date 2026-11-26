# Report logic for HR - Workforce Plan - Headcount and Budget Utilisation (runs like a Frappe non-standard Script Report).

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

names = visible("Workforce Plan", "self", can_conf)
pf = [["name", "in", list(names) or NONE]]
for k in [["company", "custom_company"], ["department", "department"], ["function", "custom_function"], ["fiscal_year", "fiscal_year"]]:
    if f.get(k[0]):
        pf.append([k[1], "=", f.get(k[0])])
if f.get("approved_only"):
    pf.append(["workflow_state", "=", "Approved"])
pf = date_filters(pf, f, "creation")
GB = {"Workforce Plan": ["name", "Workforce Plan"], "Company": ["custom_company", "Company"], "Function": ["custom_function", "Function"], "Department": ["department", "Department"], "Cost Center": ["cost_center", "Cost Center"], "Fiscal Year": ["fiscal_year", "Fiscal Year"], "Budget Line": ["budget_line", "Budget"]}
gb = f.get("group_by") or "Department"
plans = frappe.get_all("Workforce Plan", filters=pf, fields=["name", "custom_company", "custom_function", "department", "cost_center", "fiscal_year", "budget_line", "workflow_state", "approved_headcount", "approved_budget", "committed_headcount", "committed_budget", "consumed_headcount", "consumed_budget"], limit_page_length=0)
g = {}
for p in plans:
    k = p.get(GB[gb][0]) or "Not Set"
    r = g.setdefault(k, {"plans": 0, "ahc": 0, "chc": 0, "uhc": 0, "ab": 0.0, "cb": 0.0, "ub": 0.0})
    r["plans"] = r["plans"] + 1
    r["ahc"] = r["ahc"] + cint(p.approved_headcount)
    r["chc"] = r["chc"] + cint(p.committed_headcount)
    r["uhc"] = r["uhc"] + cint(p.consumed_headcount)
    r["ab"] = r["ab"] + flt(p.approved_budget)
    r["cb"] = r["cb"] + flt(p.committed_budget)
    r["ub"] = r["ub"] + flt(p.consumed_budget)
warn = flt(f.get("warn_pct") or 90)
rows = []
for k in sorted(g.keys()):
    r = g[k]
    hcp = round((r["chc"] + r["uhc"]) * 100.0 / r["ahc"], 1) if r["ahc"] else 0
    bp = round((r["cb"] + r["ub"]) * 100.0 / r["ab"], 1) if r["ab"] else 0
    flag = []
    if (r["chc"] + r["uhc"]) > r["ahc"]:
        flag.append("Headcount over plan")
    if (r["cb"] + r["ub"]) > r["ab"]:
        flag.append("Budget over plan")
    if not flag and (hcp >= warn or bp >= warn):
        flag.append("Near limit")
    if f.get("exceptions_only") and not flag:
        continue
    rows.append({"_cur": "USD", "grp": k, "plans": r["plans"], "ahc": r["ahc"], "chc": r["chc"], "uhc": r["uhc"], "rhc": r["ahc"] - r["chc"] - r["uhc"], "hcp": hcp,
        "ab": r["ab"], "cb": r["cb"], "ub": r["ub"], "rb": r["ab"] - r["cb"] - r["ub"], "bp": bp, "flag": ", ".join(flag) if flag else "OK"})
columns = [C("grp", gb, "Link", GB[gb][1], 200), C("plans", "Plans", "Int", None, 70), C("ahc", "Approved HC", "Int", None, 100), C("chc", "Committed HC", "Int", None, 110), C("uhc", "Consumed HC", "Int", None, 110), C("rhc", "Remaining HC", "Int", None, 110), C("hcp", "HC Used %", "Percent", None, 100),
    C("ab", "Approved Budget (USD)", "Currency", None, 160), C("cb", "Committed Budget (USD)", "Currency", None, 160), C("ub", "Consumed Budget (USD)", "Currency", None, 160), C("rb", "Remaining Budget (USD)", "Currency", None, 160), C("bp", "Budget Used %", "Percent", None, 110), C("flag", "Flag", "Data", None, 200)]
top = rows[:15]
chart = {"data": {"labels": [x["grp"] for x in top], "datasets": [{"name": "Approved", "values": [x["ab"] for x in top]}, {"name": "Committed", "values": [x["cb"] for x in top]}, {"name": "Consumed", "values": [x["ub"] for x in top]}]}, "type": "bar"}
T = {"ahc": 0, "chc": 0, "uhc": 0, "ab": 0, "cb": 0, "ub": 0}
for x in rows:
    for k in T:
        T[k] = T[k] + x[k]
summary = [{"value": T["ahc"], "label": "Approved HC", "datatype": "Int"}, {"value": T["chc"] + T["uhc"], "label": "Committed + Consumed HC", "datatype": "Int"}, {"value": T["ab"], "label": "Approved Budget (USD)", "datatype": "Currency", "currency": "USD"}, {"value": T["cb"] + T["ub"], "label": "Committed + Consumed (USD)", "datatype": "Currency", "currency": "USD"}]
data = columns, rows, None, chart, summary
