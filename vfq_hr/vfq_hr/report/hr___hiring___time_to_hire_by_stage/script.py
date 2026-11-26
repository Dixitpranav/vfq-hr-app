# Report logic for HR - Hiring - Time to Hire by Stage (runs like a Frappe non-standard Script Report).

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
names = visible("Job Applicant", "applicant", can_conf)
pf = [["name", "in", list(names) or NONE], ["custom_recruitment_status", "in", ["Onboarded", "Approved to onboard"] if f.get("include_approved") else ["Onboarded"]]]
for k in [["company", "custom_company"], ["department", "custom_department"], ["function", "custom_function"]]:
    if f.get(k[0]):
        pf.append([k[1], "=", f.get(k[0])])
pf = date_filters(pf, f, "custom_cv_received_date")
apps = frappe.get_all("Job Applicant", filters=pf, fields=["name", "applicant_name", "job_title", "custom_department", "custom_role_classification", "custom_cv_received_date", "custom_shortlisting_confirmation_date", "custom_onboarded_date", "custom_joining_date", "custom_employee"], limit_page_length=0)
om = {}
for o in frappe.get_all("Job Opening", filters={"name": ["in", list(set([a.job_title for a in apps if a.job_title])) or NONE]}, fields=["name", "posted_on", "job_requisition"]):
    om[o.name] = o
rm = {}
for j in frappe.get_all("Job Requisition", filters={"name": ["in", list(set([o.job_requisition for o in om.values() if o.job_requisition])) or NONE]}, fields=["name", "creation", "owner", "posting_date", "workflow_state", "custom_budget_plan"]):
    rm[j.name] = j
wm = {}
for w in frappe.get_all("Workforce Plan", filters={"name": ["in", list(set([j.custom_budget_plan for j in rm.values() if j.custom_budget_plan])) or NONE]}, fields=["name", "creation", "owner", "workflow_state"]):
    wm[w.name] = w
wh = history("Workforce Plan", list(wm.keys()), "workflow_state", wm)
jh = history("Job Requisition", list(rm.keys()), "workflow_state", rm)
def approved_at(h):
    for e in h:
        if e[0] == "Approved":
            return e[1]
    return None
emps = {}
for e in frappe.get_all("Employee", filters={"name": ["in", [a.custom_employee for a in apps if a.custom_employee] or NONE]}, fields=["name", "date_of_joining"]):
    emps[e.name] = e.date_of_joining
cx = {}
for c in frappe.get_all("CXO Hiring Approval Applicant", filters={"job_applicant": ["in", [a.name for a in apps] or NONE], "parenttype": "CXO Hiring Approval"}, fields=["job_applicant", "parent"], limit_page_length=0):
    cx[c.job_applicant] = c.parent
cxd = {}
for c in frappe.get_all("CXO Hiring Approval", filters={"name": ["in", list(set(cx.values())) or NONE]}, fields=["name", "ceo_approved_on", "modified", "workflow_state"]):
    cxd[c.name] = c.ceo_approved_on or (c.modified if c.workflow_state == "Approved to onboard" else None)
def dd(a, b):
    if not a or not b:
        return None
    return frappe.utils.date_diff(b, a)
STG = [["s1", "Plan Approval"], ["s2", "Plan Approved to JR"], ["s3", "JR Approval"], ["s4", "JR Approved to Opening"], ["s5", "Opening to CV"], ["s6", "CV to Shortlist"], ["s7", "Shortlist to CXO Approval"], ["s8", "CXO Approval to Join"], ["ttf", "Time to Fill (Opening to Join)"], ["tth", "Time to Hire (CV to Join)"]]
det = []
for a in apps:
    o = om.get(a.job_title) or {}
    j = rm.get(o.get("job_requisition")) or {}
    w = wm.get(j.get("custom_budget_plan")) or {}
    wa = approved_at(wh.get(w.get("name"), [])) if w else None
    ja_ = approved_at(jh.get(j.get("name"), [])) if j else None
    joined = emps.get(a.custom_employee) or a.custom_onboarded_date or a.custom_joining_date
    ca = cxd.get(cx.get(a.name))
    r = {"ja": a.name, "name": a.applicant_name, "jo": a.job_title, "dept": a.custom_department, "role": a.custom_role_classification, "joined": joined,
        "s1": dd(w.get("creation"), wa), "s2": dd(wa, j.get("posting_date")), "s3": dd(j.get("creation"), ja_), "s4": dd(ja_, o.get("posted_on")), "s5": dd(o.get("posted_on"), a.custom_cv_received_date),
        "s6": dd(a.custom_cv_received_date, a.custom_shortlisting_confirmation_date), "s7": dd(a.custom_shortlisting_confirmation_date, ca), "s8": dd(ca, joined),
        "ttf": dd(o.get("posted_on"), joined), "tth": dd(a.custom_cv_received_date, joined)}
    det.append(r)
gb = f.get("group_by") or "Applicant (Detail)"
if gb == "Applicant (Detail)":
    columns = [C("ja", "Job Applicant", "Link", "Job Applicant", 160), C("name", "Applicant", "Data", None, 140), C("jo", "Job Opening", "Link", "Job Opening", 150), C("dept", "Department", "Link", "Department", 140), C("joined", "Joined On", "Date", None, 100)]
    for s in STG:
        columns.append(C(s[0], s[1] + " (Days)", "Int", None, 150))
    data = columns, det
else:
    key = {"Department": "dept", "Role Classification": "role"}[gb]
    g = {}
    for r in det:
        g.setdefault(r.get(key) or "Not Set", []).append(r)
    def med(v):
        v = sorted(v)
        n = len(v)
        if not n:
            return None
        return v[n // 2] if n % 2 else round((v[n // 2 - 1] + v[n // 2]) / 2.0, 1)
    out = []
    for k in sorted(g.keys()):
        row = {"grp": k, "hires": len(g[k])}
        for s in STG:
            vals = []
            for x in g[k]:
                if x.get(s[0]) is not None:
                    vals.append(x.get(s[0]))
            row[s[0]] = med(vals)
        out.append(row)
    columns = [C("grp", gb, "Data", None, 180), C("hires", "Hires", "Int", None, 80)]
    for s in STG:
        columns.append(C(s[0], "Median " + s[1] + " (Days)", "Float", None, 170))
    data = columns, out
