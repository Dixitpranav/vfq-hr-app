# Report logic for HR - Job Applicant - Recruitment Funnel (runs like a Frappe non-standard Script Report).

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
pf = [["name", "in", list(names) or NONE]]
if f.get("company"):
    pf.append(["custom_company", "=", f.get("company")])
if f.get("department"):
    pf.append(["custom_department", "=", f.get("department")])
if f.get("function"):
    pf.append(["custom_function", "=", f.get("function")])
if f.get("job_opening"):
    pf.append(["job_title", "=", f.get("job_opening")])
pf = date_filters(pf, f, "custom_cv_received_date")
apps = frappe.get_all("Job Applicant", filters=pf, fields=["name", "creation", "owner", "job_title", "custom_department", "custom_function", "source", "custom_role_classification", "custom_hiring_manager", "custom_recruitment_status", "custom_interview_date", "custom_shortlisting_confirmation_date", "custom_employee"], limit_page_length=0)
am = {}
for a in apps:
    am[a.name] = a
hist = history("Job Applicant", list(am.keys()), "custom_recruitment_status", am)
LV = {"Open": 0, "Interview Scheduled": 1, "Shortlisted": 2, "Approved to onboard": 3, "Onboarded": 4}
GB = {"Job Opening": "job_title", "Department": "custom_department", "Function": "custom_function", "Source": "source", "Role Classification": "custom_role_classification", "Hiring Manager": "custom_hiring_manager"}
GL = {"Job Opening": "Job Opening", "Department": "Department", "Function": "Function", "Source": "Job Applicant Source", "Role Classification": "Designation", "Hiring Manager": "Employee"}
gb = f.get("group_by") or "Job Opening"
g = {}
for a in apps:
    reached = 0
    for e in hist[a.name]:
        reached = max(reached, LV.get(e[0], 0))
    reached = max(reached, LV.get(a.custom_recruitment_status, 0))
    if a.custom_interview_date:
        reached = max(reached, 1)
    if a.custom_shortlisting_confirmation_date:
        reached = max(reached, 2)
    if a.custom_employee:
        reached = 4
    k = a.get(GB[gb]) or "Not Set"
    r = g.setdefault(k, {"total": 0, "l1": 0, "l2": 0, "l3": 0, "l4": 0, "rej": 0, "bo": 0, "active": 0})
    r["total"] = r["total"] + 1
    for i in [1, 2, 3, 4]:
        if reached >= i:
            r["l" + str(i)] = r["l" + str(i)] + 1
    if a.custom_recruitment_status == "Rejected":
        r["rej"] = r["rej"] + 1
    elif a.custom_recruitment_status == "Backed-Off":
        r["bo"] = r["bo"] + 1
    elif a.custom_recruitment_status != "Onboarded":
        r["active"] = r["active"] + 1

def pc(a, b):
    return round(a * 100.0 / b, 1) if b else 0

rows = []
for k in sorted(g.keys()):
    r = g[k]
    rows.append({"grp": k, "total": r["total"], "l1": r["l1"], "l2": r["l2"], "l3": r["l3"], "l4": r["l4"], "rej": r["rej"], "bo": r["bo"], "active": r["active"],
        "c1": pc(r["l1"], r["total"]), "c2": pc(r["l2"], r["l1"]), "c3": pc(r["l3"], r["l2"]), "c4": pc(r["l4"], r["l3"]), "co": pc(r["l4"], r["total"])})
T = {"total": 0, "l1": 0, "l2": 0, "l3": 0, "l4": 0}
for r in rows:
    for k in T:
        T[k] = T[k] + r[k]
columns = [C("grp", gb, "Link", GL[gb], 200), C("total", "Applicants", "Int", None, 90), C("l1", "Reached Interview", "Int", None, 120), C("l2", "Reached Shortlist", "Int", None, 120), C("l3", "Approved to Onboard", "Int", None, 130), C("l4", "Onboarded", "Int", None, 90),
    C("c1", "Applied to Interview %", "Percent", None, 140), C("c2", "Interview to Shortlist %", "Percent", None, 150), C("c3", "Shortlist to Approval %", "Percent", None, 150), C("c4", "Approval to Join %", "Percent", None, 130), C("co", "Overall Conversion %", "Percent", None, 140),
    C("active", "Still In Process", "Int", None, 110), C("rej", "Rejected", "Int", None, 80), C("bo", "Backed-Off", "Int", None, 90)]
chart = {"data": {"labels": ["Applied", "Interview", "Shortlisted", "Approved", "Onboarded"], "datasets": [{"name": "Applicants", "values": [T["total"], T["l1"], T["l2"], T["l3"], T["l4"]]}]}, "type": "bar"}
summary = [{"value": T["total"], "label": "Applicants", "datatype": "Int"}, {"value": T["l2"], "label": "Reached Shortlist", "datatype": "Int"}, {"value": T["l4"], "label": "Onboarded", "datatype": "Int", "indicator": "Green"}, {"value": pc(T["l4"], T["total"]), "label": "Overall Conversion %", "datatype": "Percent"}]
data = columns, rows, None, chart, summary
