# Report logic for HR - Hiring - End-to-End Traceability (runs like a Frappe non-standard Script Report).

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
Q = json.loads("\"\\nselect\\n  ja.name as \\\"Job Applicant:Link/Job Applicant:180\\\",\\n  ja.applicant_name as \\\"Candidate:Data:150\\\",\\n  ja.custom_function as \\\"Function:Link/Function:130\\\",\\n  ja.custom_sub_function as \\\"Sub Function:Link/Function:140\\\",\\n  ja.custom_department as \\\"Department:Link/Department:150\\\",\\n  ja.custom_role_classification as \\\"Role Classification:Link/Designation:150\\\",\\n  ja.custom_hiring_type as \\\"Hiring Type:Data:100\\\",\\n  ja.custom_recruitment_status as \\\"Recruitment Status:Data:140\\\",\\n  ja.custom_agreed_salary as \\\"Agreed Salary (USD):Currency:120\\\",\\n  ja.custom_vendor as \\\"Vendor:Link/Supplier:150\\\",\\n  ja.custom_project as \\\"Project:Link/Project:120\\\",\\n  wp.name as \\\"Workforce Plan:Link/Workforce Plan:150\\\",\\n  wp.workflow_state as \\\"WP Status:Data:100\\\",\\n  wp.approved_headcount as \\\"WP Approved Headcount:Data:100\\\",\\n  wp.approved_budget as \\\"WP Approved Budget:Data:100\\\",\\n  wp.committed_headcount as \\\"WP Committed Headcount:Data:100\\\",\\n  wp.consumed_headcount as \\\"WP Consumed Headcount:Data:100\\\",\\n  jr.name as \\\"Job Requisition:Link/Job Requisition:150\\\",\\n  jr.workflow_state as \\\"JR Workflow State:Data:140\\\",\\n  jr.custom_annual_budget_impact as \\\"JR Annual Budget Impact (USD):Currency:150\\\",\\n  jr.no_of_positions as \\\"JR Total Positions:Int:100\\\",\\n  jo.name as \\\"Job Opening:Link/Job Opening:150\\\",\\n  jo.status as \\\"JO Status:Data:100\\\",\\n  emp.name as \\\"Employee:Link/Employee:130\\\",\\n  emp.status as \\\"Employee Status:Data:110\\\",\\n  emp.date_of_joining as \\\"Date of Joining:Date:110\\\",\\n  emp.ctc as \\\"CTC:Currency:110\\\",\\n  emp.relieving_date as \\\"Relieving Date:Date:110\\\",\\n  pr.decision as \\\"Probation Decision:Data:130\\\",\\n  pr.overall_rating as \\\"Probation Rating:Data:100\\\",\\n  pr.review_date as \\\"Probation Review Date:Date:130\\\",\\n  myr.overall_assessment as \\\"Mid-Year Assessment:Data:140\\\",\\n  myr.review_period as \\\"Mid-Year Period:Data:100\\\",\\n  myr.review_year as \\\"Mid-Year Year:Data:100\\\",\\n  apr.final_rating as \\\"Annual Final Rating:Float:110\\\",\\n  apr.performance_band as \\\"Annual Performance Band:Data:150\\\",\\n  apr.promotion_recommendation as \\\"Promotion Recommended:Check:120\\\",\\n  ee.exit_type as \\\"Exit Type:Data:120\\\",\\n  ee.last_working_day as \\\"Last Working Day:Date:120\\\",\\n  ee.offboarding_status as \\\"Offboarding Status:Data:150\\\",\\n  ee.rehire_eligible as \\\"Rehire Eligible:Check:110\\\"\\nfrom `tabJob Applicant` ja\\nleft join `tabEmployee` emp on emp.name = ja.custom_employee\\nleft join `tabJob Opening` jo on jo.name = ja.job_title\\nleft join `tabJob Requisition` jr on jr.name = jo.job_requisition\\nleft join `tabWorkforce Plan` wp on wp.name = jr.custom_budget_plan\\nleft join `tabProbation Review` pr on pr.name = (\\n  select p2.name from `tabProbation Review` p2 where p2.employee = emp.name order by p2.review_date desc, p2.creation desc limit 1\\n)\\nleft join `tabMid-Year Review` myr on myr.name = (\\n  select m2.name from `tabMid-Year Review` m2 where m2.employee = emp.name order by m2.creation desc limit 1\\n)\\nleft join `tabAnnual Performance Review` apr on apr.name = (\\n  select a2.name from `tabAnnual Performance Review` a2 where a2.employee = emp.name order by a2.review_year desc, a2.creation desc limit 1\\n)\\nleft join `tabEmployee Exit` ee on ee.employee = emp.name\\norder by ja.creation desc\\n\"")
OC = json.loads("[{\"label\":\"Job Applicant\",\"fieldtype\":\"Link\",\"options\":\"Job Applicant\",\"width\":180},{\"label\":\"Candidate\",\"fieldtype\":\"Data\",\"options\":null,\"width\":150},{\"label\":\"Function\",\"fieldtype\":\"Link\",\"options\":\"Function\",\"width\":130},{\"label\":\"Sub Function\",\"fieldtype\":\"Link\",\"options\":\"Function\",\"width\":140},{\"label\":\"Department\",\"fieldtype\":\"Link\",\"options\":\"Department\",\"width\":150},{\"label\":\"Role Classification\",\"fieldtype\":\"Link\",\"options\":\"Designation\",\"width\":150},{\"label\":\"Hiring Type\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"Recruitment Status\",\"fieldtype\":\"Data\",\"options\":null,\"width\":140},{\"label\":\"Agreed Salary (USD)\",\"fieldtype\":\"Currency\",\"options\":null,\"width\":120},{\"label\":\"Vendor\",\"fieldtype\":\"Link\",\"options\":\"Supplier\",\"width\":150},{\"label\":\"Project\",\"fieldtype\":\"Link\",\"options\":\"Project\",\"width\":120},{\"label\":\"Workforce Plan\",\"fieldtype\":\"Link\",\"options\":\"Workforce Plan\",\"width\":150},{\"label\":\"WP Status\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"WP Approved Headcount\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"WP Approved Budget\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"WP Committed Headcount\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"WP Consumed Headcount\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"Job Requisition\",\"fieldtype\":\"Link\",\"options\":\"Job Requisition\",\"width\":150},{\"label\":\"JR Workflow State\",\"fieldtype\":\"Data\",\"options\":null,\"width\":140},{\"label\":\"JR Annual Budget Impact (USD)\",\"fieldtype\":\"Currency\",\"options\":null,\"width\":150},{\"label\":\"JR Total Positions\",\"fieldtype\":\"Int\",\"options\":null,\"width\":100},{\"label\":\"Job Opening\",\"fieldtype\":\"Link\",\"options\":\"Job Opening\",\"width\":150},{\"label\":\"JO Status\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"Employee\",\"fieldtype\":\"Link\",\"options\":\"Employee\",\"width\":130},{\"label\":\"Employee Status\",\"fieldtype\":\"Data\",\"options\":null,\"width\":110},{\"label\":\"Date of Joining\",\"fieldtype\":\"Date\",\"options\":null,\"width\":110},{\"label\":\"CTC\",\"fieldtype\":\"Currency\",\"options\":null,\"width\":110},{\"label\":\"Relieving Date\",\"fieldtype\":\"Date\",\"options\":null,\"width\":110},{\"label\":\"Probation Decision\",\"fieldtype\":\"Data\",\"options\":null,\"width\":130},{\"label\":\"Probation Rating\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"Probation Review Date\",\"fieldtype\":\"Date\",\"options\":null,\"width\":130},{\"label\":\"Mid-Year Assessment\",\"fieldtype\":\"Data\",\"options\":null,\"width\":140},{\"label\":\"Mid-Year Period\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"Mid-Year Year\",\"fieldtype\":\"Data\",\"options\":null,\"width\":100},{\"label\":\"Annual Final Rating\",\"fieldtype\":\"Float\",\"options\":null,\"width\":110},{\"label\":\"Annual Performance Band\",\"fieldtype\":\"Data\",\"options\":null,\"width\":150},{\"label\":\"Promotion Recommended\",\"fieldtype\":\"Check\",\"options\":null,\"width\":120},{\"label\":\"Exit Type\",\"fieldtype\":\"Data\",\"options\":null,\"width\":120},{\"label\":\"Last Working Day\",\"fieldtype\":\"Date\",\"options\":null,\"width\":120},{\"label\":\"Offboarding Status\",\"fieldtype\":\"Data\",\"options\":null,\"width\":150},{\"label\":\"Rehire Eligible\",\"fieldtype\":\"Check\",\"options\":null,\"width\":110}]")
names = visible("Job Applicant", "applicant", can_conf)
raw = frappe.db.sql(Q)
rows = []
apps = []
for t in raw:
    if t[0] not in names:
        continue
    r = {}
    i = 0
    for v in t:
        r["c" + str(i)] = v
        i += 1
    rows.append(r)
    apps.append(t[0])
an = apps or NONE
jm = {}
for a in frappe.get_all("Job Applicant", filters={"name": ["in", an]}, fields=["name", "job_title", "custom_company", "custom_cv_received_date", "custom_shortlisting_confirmation_date", "custom_onboarded_date"], limit_page_length=0):
    jm[a.name] = a
om = {}
for o in frappe.get_all("Job Opening", filters={"name": ["in", list(set([a.job_title for a in jm.values() if a.job_title])) or NONE]}, fields=["name", "posted_on", "job_requisition"]):
    om[o.name] = o
rm = {}
for j in frappe.get_all("Job Requisition", filters={"name": ["in", list(set([o.job_requisition for o in om.values() if o.job_requisition])) or NONE]}, fields=["name", "posting_date", "custom_budget_plan"]):
    rm[j.name] = j
wm = {}
for w in frappe.get_all("Workforce Plan", filters={"name": ["in", list(set([j.custom_budget_plan for j in rm.values() if j.custom_budget_plan])) or NONE]}, fields=["name", "creation"]):
    wm[w.name] = w
cxo = {}
for c in frappe.get_all("CXO Hiring Approval Applicant", filters={"job_applicant": ["in", an], "parenttype": "CXO Hiring Approval"}, fields=["job_applicant", "parent", "creation"], order_by="creation asc", limit_page_length=0):
    cxo[c.job_applicant] = c.parent
cm = {}
for c in frappe.get_all("CXO Hiring Approval", filters={"name": ["in", list(set(cxo.values())) or NONE]}, fields=["name", "workflow_state", "ceo_approved_on"]):
    cm[c.name] = c
out = []
for r in rows:
    a = jm.get(r["c0"]) or {}
    if f.get("company") and a.get("custom_company") != f.get("company"):
        continue
    o = om.get(a.get("job_title")) or {}
    j = rm.get(o.get("job_requisition")) or {}
    w = wm.get(j.get("custom_budget_plan")) or {}
    cn = cxo.get(r["c0"])
    c = cm.get(cn) or {}
    if f.get("from_date") and (not a.get("custom_cv_received_date") or str(a.get("custom_cv_received_date")) < str(f.get("from_date"))):
        continue
    if f.get("to_date") and (not a.get("custom_cv_received_date") or str(a.get("custom_cv_received_date")) > str(f.get("to_date"))):
        continue
    r["x_cxo"] = cn
    r["x_cxo_state"] = c.get("workflow_state")
    r["d_wp"] = w.get("creation")
    r["d_jr"] = j.get("posting_date")
    r["d_jo"] = o.get("posted_on")
    r["d_cv"] = a.get("custom_cv_received_date")
    r["d_sl"] = a.get("custom_shortlisting_confirmation_date")
    r["d_cxo"] = c.get("ceo_approved_on")
    r["d_onb"] = a.get("custom_onboarded_date")
    out.append(r)
columns = []
i = 0
for c in OC:
    d = {"fieldname": "c" + str(i), "label": c["label"], "fieldtype": c["fieldtype"], "width": c["width"]}
    if c.get("options"):
        d["options"] = c["options"]
    columns.append(d)
    i += 1
    if c["label"] == "Job Opening":
        columns.append(C("x_cxo", "CXO Hiring Approval", "Link", "CXO Hiring Approval", 160))
        columns.append(C("x_cxo_state", "CXO Status", "Data", None, 150))
columns += [C("d_wp", "Plan Created On", "Datetime", None, 140), C("d_jr", "JR Posting Date", "Date", None, 120), C("d_jo", "Opening Posted On", "Date", None, 130), C("d_cv", "CV Received", "Date", None, 110), C("d_sl", "Shortlisted On", "Date", None, 110), C("d_cxo", "CXO Final Approval On", "Datetime", None, 150), C("d_onb", "Onboarded On", "Date", None, 110)]
data = columns, out
