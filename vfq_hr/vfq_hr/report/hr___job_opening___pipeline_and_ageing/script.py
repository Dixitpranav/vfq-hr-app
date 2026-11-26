# Report logic for HR - Job Opening - Pipeline and Ageing (runs like a Frappe non-standard Script Report).

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
names = visible("Job Opening", "self", can_conf)
pf = [["name", "in", list(names) or NONE]]
for k in [["company", "company"], ["department", "department"], ["function", "custom_function"], ["status", "status"]]:
    if f.get(k[0]):
        pf.append([k[1], "=", f.get(k[0])])
pf = date_filters(pf, f, "posted_on")
ops = frappe.get_all("Job Opening", filters=pf, fields=["name", "job_title", "custom_role_classification", "department", "job_requisition", "status", "posted_on", "closes_on", "closed_on", "planned_vacancies", "vacancies", "custom_confidential_hiring"], order_by="posted_on desc, creation desc", limit_page_length=0)
on = [o.name for o in ops] or NONE
STS = ["Open", "Interview Scheduled", "Shortlisted", "Approved to onboard", "Onboarded", "Rejected", "Backed-Off"]
cnt = {}
last = {}
for a in frappe.get_all("Job Applicant", filters={"job_title": ["in", on]}, fields=["job_title", "custom_recruitment_status", "modified"], limit_page_length=0):
    c = cnt.setdefault(a.job_title, {})
    c[a.custom_recruitment_status or "Open"] = c.get(a.custom_recruitment_status or "Open", 0) + 1
    if not last.get(a.job_title) or str(a.modified) > str(last.get(a.job_title)):
        last[a.job_title] = a.modified
stall = cint(f.get("stall_days") or 14)
rows = []
for o in ops:
    c = cnt.get(o.name, {})
    vac = cint(o.planned_vacancies) or cint(o.vacancies)
    total = sum(c.values())
    la = last.get(o.name)
    idle = frappe.utils.date_diff(today, la) if la else (frappe.utils.date_diff(today, o.posted_on) if o.posted_on else None)
    stalled = "Yes" if o.status == "Open" and idle is not None and idle > stall else ""
    if f.get("stalled_only") and not stalled:
        continue
    row = {"jo": o.name, "title": o.job_title, "role": o.custom_role_classification, "dept": o.department, "jr": o.job_requisition, "status": o.status, "posted_on": o.posted_on, "closes_on": o.closes_on,
        "days_open": frappe.utils.date_diff(o.closed_on or today, o.posted_on) if o.posted_on else None, "vac": vac, "total": total, "remaining": max(vac - c.get("Onboarded", 0), 0),
        "last_activity": la, "idle": idle, "stalled": stalled, "overdue": "Yes" if o.status == "Open" and o.closes_on and str(o.closes_on) < today else ""}
    for s in STS:
        row["s_" + s.lower().replace(" ", "_").replace("-", "_")] = c.get(s, 0)
    rows.append(row)
columns = [C("jo", "Job Opening", "Link", "Job Opening", 170), C("title", "Job Title", "Data", None, 170), C("role", "Role Classification", "Link", "Designation", 150), C("dept", "Department", "Link", "Department", 150), C("jr", "Job Requisition", "Link", "Job Requisition", 160),
    C("status", "Status", "Data", None, 80), C("posted_on", "Posted On", "Date", None, 100), C("closes_on", "Closes On", "Date", None, 100), C("days_open", "Days Open", "Int", None, 90), C("overdue", "Past Closing Date", "Data", None, 110),
    C("vac", "Vacancies", "Int", None, 90), C("total", "Applicants", "Int", None, 90)]
for s in STS:
    columns.append(C("s_" + s.lower().replace(" ", "_").replace("-", "_"), s, "Int", None, 110))
columns += [C("remaining", "Vacancies Remaining", "Int", None, 130), C("last_activity", "Last Applicant Activity", "Datetime", None, 150), C("idle", "Days Since Activity", "Int", None, 120), C("stalled", "Stalled", "Data", None, 80)]
data = columns, rows
