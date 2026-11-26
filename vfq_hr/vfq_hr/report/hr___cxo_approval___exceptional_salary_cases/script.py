# Report logic for HR - CXO Approval - Exceptional Salary Cases (runs like a Frappe non-standard Script Report).

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
names = visible("CXO Hiring Approval", "cxo", can_conf)
pf = [["name", "in", list(names) or NONE]]
if f.get("company"):
    pf.append(["company", "=", f.get("company")])
if f.get("state"):
    pf.append(["workflow_state", "=", f.get("state")])
pf = date_filters(pf, f, "creation")
cx = frappe.get_all("CXO Hiring Approval", filters=pf, fields=["name", "title", "company", "workflow_state", "creation", "ceo_approved_by", "ceo_approved_on"], limit_page_length=0)
cm = {}
for c in cx:
    cm[c.name] = c
cn = list(cm.keys()) or NONE
ex = frappe.get_all("CXO Exceptional Approval", filters={"parent": ["in", cn]}, fields=["parent", "idx", "position", "custom_position_title", "function", "type", "recommended_salary_range", "monthly_cost_impact", "hr_comments", "approved_role_count"], order_by="parent desc, idx asc", limit_page_length=0)
apps = frappe.get_all("CXO Hiring Approval Applicant", filters={"parent": ["in", cn]}, fields=["parent", "position", "job_applicant", "applicant_name", "agreed_salary_usd"], limit_page_length=0)
am = {}
for a in apps:
    am.setdefault((a.parent, a.position), []).append(a)
ja = list(set([a.job_applicant for a in apps if a.job_applicant])) or NONE
j2o = {}
for j in frappe.get_all("Job Applicant", filters={"name": ["in", ja]}, fields=["name", "job_title"]):
    j2o[j.name] = j.job_title
om = {}
for o in frappe.get_all("Job Opening", filters={"name": ["in", list(set(j2o.values())) or NONE]}, fields=["name", "upper_range"]):
    om[o.name] = flt(o.upper_range)
rows = []
for e in ex:
    c = cm.get(e.parent)
    lst = am.get((e.parent, e.position)) or [None]
    for a in lst:
        hi = om.get(j2o.get(a.job_applicant)) if a else None
        sal = flt(a.agreed_salary_usd) if a else 0
        rows.append({"_cur": "USD", "cxo": e.parent, "title": c.title, "company": c.company, "state": c.workflow_state, "pos": e.custom_position_title or e.position, "func": e.function, "type": e.type,
            "range": e.recommended_salary_range, "impact": e.monthly_cost_impact, "ja": a.job_applicant if a else None, "an": a.applicant_name if a else None, "sal": sal or None, "hi": hi,
            "above": (sal - hi) if (sal and hi and sal > hi) else None, "above_pct": round((sal - hi) * 100.0 / hi, 1) if (sal and hi and sal > hi) else None,
            "hr": e.hr_comments, "by": c.ceo_approved_by, "on": c.ceo_approved_on})
columns = [C("cxo", "CXO Hiring Approval", "Link", "CXO Hiring Approval", 170), C("title", "Title", "Data", None, 160), C("company", "Company", "Link", "Company", 130), C("state", "Status", "Data", None, 160),
    C("pos", "Position", "Data", None, 160), C("func", "Function", "Link", "Function", 130), C("type", "Exception Type", "Data", None, 130), C("range", "Recommended Salary Range", "Data", None, 170), C("impact", "Monthly Cost Impact (USD)", "Currency", None, 160),
    C("ja", "Job Applicant", "Link", "Job Applicant", 160), C("an", "Applicant", "Data", None, 150), C("sal", "Agreed Salary (USD)", "Currency", None, 140), C("hi", "Salary Range Max (USD)", "Currency", None, 120), C("above", "Above Range (USD)", "Currency", None, 130), C("above_pct", "Above Range %", "Percent", None, 100),
    C("hr", "HR Comments", "Data", None, 220), C("by", "Final Approver", "Data", None, 150), C("on", "Final Approved On", "Datetime", None, 150)]
data = columns, rows
