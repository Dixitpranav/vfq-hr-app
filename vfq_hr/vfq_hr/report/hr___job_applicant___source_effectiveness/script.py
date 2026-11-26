# Report logic for HR - Job Applicant - Source Effectiveness (runs like a Frappe non-standard Script Report).

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
apps = frappe.get_all("Job Applicant", filters=pf, fields=["name", "source", "custom_vendor", "custom_recruitment_status", "custom_shortlisting_confirmation_date", "custom_cv_received_date", "custom_onboarded_date", "custom_joining_date", "custom_employee", "custom_total_recruitment_expense"], limit_page_length=0)
LV = {"Open": 0, "Interview Scheduled": 1, "Shortlisted": 2, "Approved to onboard": 3, "Onboarded": 4}
by_vendor = f.get("split_vendor")
g = {}
for a in apps:
    k = (a.source or "Not Set") + ((" / " + a.custom_vendor) if (by_vendor and a.custom_vendor) else "")
    r = g.setdefault(k, {"cv": 0, "short": 0, "onb": 0, "bo": 0, "rej": 0, "days": [], "cost": 0})
    r["cv"] = r["cv"] + 1
    lvl = LV.get(a.custom_recruitment_status, 0)
    if lvl >= 2 or a.custom_shortlisting_confirmation_date:
        r["short"] = r["short"] + 1
    if lvl == 4 or a.custom_employee:
        r["onb"] = r["onb"] + 1
        dj = a.custom_onboarded_date or a.custom_joining_date
        if dj and a.custom_cv_received_date:
            r["days"].append(frappe.utils.date_diff(dj, a.custom_cv_received_date))
    if a.custom_recruitment_status == "Backed-Off":
        r["bo"] = r["bo"] + 1
    if a.custom_recruitment_status == "Rejected":
        r["rej"] = r["rej"] + 1
    r["cost"] = r["cost"] + flt(a.custom_total_recruitment_expense)
rows = []
for k in sorted(g.keys()):
    r = g[k]
    rows.append({"_cur": "USD", "src": k, "cv": r["cv"], "short": r["short"], "onb": r["onb"], "bo": r["bo"], "rej": r["rej"],
        "sr": round(r["short"] * 100.0 / r["cv"], 1) if r["cv"] else 0, "hr": round(r["onb"] * 100.0 / r["cv"], 1) if r["cv"] else 0,
        "avg": round(sum(r["days"]) * 1.0 / len(r["days"]), 1) if r["days"] else None, "cost": r["cost"], "cph": round(r["cost"] / r["onb"], 2) if r["onb"] else None})
columns = [C("src", "Source" + (" / Vendor" if by_vendor else ""), "Data", None, 220), C("cv", "CVs Received", "Int", None, 100), C("short", "Shortlisted", "Int", None, 100), C("onb", "Hired", "Int", None, 80), C("bo", "Backed-Off", "Int", None, 90), C("rej", "Rejected", "Int", None, 80),
    C("sr", "Shortlist Rate %", "Percent", None, 120), C("hr", "Hire Rate %", "Percent", None, 100), C("avg", "Avg Days CV to Join", "Float", None, 130), C("cost", "Recruitment Expense (USD)", "Currency", None, 170), C("cph", "Cost per Hire (USD)", "Currency", None, 140)]
chart = {"data": {"labels": [r["src"] for r in rows], "datasets": [{"name": "CVs", "values": [r["cv"] for r in rows]}, {"name": "Hired", "values": [r["onb"] for r in rows]}]}, "type": "bar"}
data = columns, rows, None, chart
