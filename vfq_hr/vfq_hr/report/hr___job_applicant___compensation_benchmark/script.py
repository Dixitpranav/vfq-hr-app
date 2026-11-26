# Report logic for HR - Job Applicant - Compensation Benchmark (runs like a Frappe non-standard Script Report).

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
if f.get("agreed_only"):
    pf.append(["custom_agreed_salary", ">", 0])
apps = frappe.get_all("Job Applicant", filters=pf, fields=["name", "applicant_name", "job_title", "custom_role_classification", "custom_department", "custom_recruitment_status", "custom_expected_salary", "custom_agreed_salary", "lower_range", "upper_range", "custom_exceptional_salary_case", "custom_ctc_total", "custom_ctc_total_monthly"], order_by="creation desc", limit_page_length=0)
om = {}
for o in frappe.get_all("Job Opening", filters={"name": ["in", list(set([a.job_title for a in apps if a.job_title])) or NONE]}, fields=["name", "lower_range", "custom_mid_range", "upper_range"]):
    om[o.name] = o
rows = []
for a in apps:
    o = om.get(a.job_title) or {}
    lo = flt(o.get("lower_range")) or flt(a.lower_range)
    hi = flt(o.get("upper_range")) or flt(a.upper_range)
    mid = flt(o.get("custom_mid_range")) or ((lo + hi) / 2.0 if (lo and hi) else 0)
    sal = flt(a.custom_agreed_salary) or flt(a.custom_expected_salary)
    basis = "Agreed" if flt(a.custom_agreed_salary) else ("Expected" if flt(a.custom_expected_salary) else "")
    pos = ""
    if sal and hi and sal > hi:
        pos = "Above range"
    elif sal and lo and sal < lo:
        pos = "Below range"
    elif sal and (lo or hi):
        pos = "Within range"
    if f.get("position") and f.get("position") != pos:
        continue
    rows.append({"_cur": "USD", "ja": a.name, "name": a.applicant_name, "jo": a.job_title, "role": a.custom_role_classification, "dept": a.custom_department, "status": a.custom_recruitment_status,
        "lo": lo, "mid": mid, "hi": hi, "exp": a.custom_expected_salary, "agr": a.custom_agreed_salary, "basis": basis, "compa": round(sal / mid, 2) if (sal and mid) else None,
        "vs_mid": round((sal - mid) * 100.0 / mid, 1) if (sal and mid) else None, "above_max": (sal - hi) if (sal and hi and sal > hi) else 0, "pos": pos,
        "exc": "Yes" if a.custom_exceptional_salary_case else "", "ctc": a.custom_ctc_total, "ctc_m": a.custom_ctc_total_monthly})
columns = [C("ja", "Job Applicant", "Link", "Job Applicant", 170), C("name", "Applicant", "Data", None, 150), C("jo", "Job Opening", "Link", "Job Opening", 160), C("role", "Role Classification", "Link", "Designation", 150), C("dept", "Department", "Link", "Department", 140),
    C("status", "Recruitment Status", "Data", None, 140),
    C("lo", "Salary Range Low (USD)", "Currency", None, 120), C("mid", "Salary Range Mid (USD)", "Currency", None, 120), C("hi", "Salary Range Max (USD)", "Currency", None, 120), C("exp", "Expected Salary (USD)", "Currency", None, 140), C("agr", "Agreed Salary (USD)", "Currency", None, 140),
    C("basis", "Benchmarked On", "Data", None, 110), C("compa", "Compa-Ratio", "Float", None, 100), C("vs_mid", "vs Mid %", "Percent", None, 90), C("pos", "Position in Range", "Data", None, 120), C("above_max", "Above Max (USD)", "Currency", None, 120),
    C("exc", "Exceptional Case", "Data", None, 110), C("ctc", "Total CTC (USD)", "Currency", None, 120), C("ctc_m", "Total CTC Monthly (USD)", "Currency", None, 150)]
data = columns, rows
