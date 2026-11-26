# Report logic for HR - Onboarding - Joining Pipeline (runs like a Frappe non-standard Script Report).

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
sts = ["Approved to onboard", "Backed-Off"] + (["Onboarded"] if f.get("include_onboarded") else [])
pf = [["name", "in", list(names) or NONE], ["custom_recruitment_status", "in", sts]]
for k in [["company", "custom_company"], ["department", "custom_department"], ["function", "custom_function"]]:
    if f.get(k[0]):
        pf.append([k[1], "=", f.get(k[0])])
pf = date_filters(pf, f, "custom_joining_date")
apps = frappe.get_all("Job Applicant", filters=pf, fields=["name", "applicant_name", "job_title", "custom_role_classification", "custom_department", "custom_hiring_manager", "custom_employment_type", "custom_hiring_type", "custom_recruitment_status", "custom_cxo_approval_status", "custom_joining_date", "custom_joining_month", "custom_current_notice_period", "custom_agreed_salary", "custom_employee", "custom_onboarded_date"], order_by="custom_joining_date asc", limit_page_length=0)
rows = []
for a in apps:
    d = frappe.utils.date_diff(a.custom_joining_date, today) if a.custom_joining_date else None
    flag = ""
    if a.custom_recruitment_status == "Approved to onboard":
        if d is None:
            flag = "No joining date"
        elif d < 0:
            flag = "Joining date passed"
        elif d <= 7:
            flag = "Joining within 7 days"
    rows.append({"_cur": "USD", "ja": a.name, "name": a.applicant_name, "jo": a.job_title, "role": a.custom_role_classification, "dept": a.custom_department, "hm": a.custom_hiring_manager, "et": a.custom_employment_type, "ht": a.custom_hiring_type,
        "status": a.custom_recruitment_status, "cxo": a.custom_cxo_approval_status, "jd": a.custom_joining_date, "jm": a.custom_joining_month, "np": a.custom_current_notice_period, "dtj": d, "flag": flag, "sal": a.custom_agreed_salary, "emp": a.custom_employee})
# KPIs over all visible applicants
allv = frappe.get_all("Job Applicant", filters={"name": ["in", list(names) or NONE], "custom_recruitment_status": ["in", ["Approved to onboard", "Backed-Off", "Onboarded"]]}, fields=["custom_recruitment_status"], limit_page_length=0)
kp = {"Approved to onboard": 0, "Backed-Off": 0, "Onboarded": 0}
for x in allv:
    kp[x.custom_recruitment_status] = kp[x.custom_recruitment_status] + 1
offers = kp["Approved to onboard"] + kp["Backed-Off"] + kp["Onboarded"]
summary = [{"value": kp["Approved to onboard"], "label": "Awaiting Joining", "datatype": "Int", "indicator": "Blue"}, {"value": kp["Onboarded"], "label": "Joined", "datatype": "Int", "indicator": "Green"},
    {"value": kp["Backed-Off"], "label": "Backed-Off", "datatype": "Int", "indicator": "Red"}, {"value": round(kp["Onboarded"] * 100.0 / offers, 1) if offers else 0, "label": "Offer-to-Join %", "datatype": "Percent"}]
columns = [C("ja", "Job Applicant", "Link", "Job Applicant", 170), C("name", "Applicant", "Data", None, 150), C("jo", "Job Opening", "Link", "Job Opening", 160), C("role", "Role Classification", "Link", "Designation", 150), C("dept", "Department", "Link", "Department", 140), C("hm", "Hiring Manager", "Link", "Employee", 140),
    C("et", "Employment Type", "Data", None, 120), C("ht", "Hiring Type", "Data", None, 100), C("status", "Status", "Data", None, 150), C("cxo", "CXO Approval Status", "Data", None, 140), C("jd", "Planned Joining Date", "Date", None, 130), C("jm", "Joining Month", "Data", None, 110),
    C("dtj", "Days to Join", "Int", None, 100), C("flag", "Alert", "Data", None, 160), C("np", "Notice Period", "Data", None, 110), C("sal", "Agreed Salary (USD)", "Currency", None, 140), C("emp", "Employee", "Link", "Employee", 130)]
data = columns, rows, None, None, summary
