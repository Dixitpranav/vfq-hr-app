# Report logic for HR - Workforce Plan - Approval Ageing (runs like a Frappe non-standard Script Report).

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

CFG = json.loads("{\"dt\":\"Workforce Plan\",\"sf\":\"workflow_state\",\"mode\":\"self\",\"label\":\"Workforce Plan\",\"finals\":[\"Approved\",\"Rejected\"],\"fmap\":{\"company\":\"custom_company\",\"department\":\"department\",\"function\":\"custom_function\",\"fiscal_year\":\"fiscal_year\"},\"info\":[[\"custom_company\",\"Company\",\"Link\",\"Company\"],[\"department\",\"Department\",\"Link\",\"Department\"],[\"custom_function\",\"Function\",\"Link\",\"Function\"],[\"fiscal_year\",\"Fiscal Year\",\"Link\",\"Fiscal Year\"]],\"stages\":[[\"Draft\",\"Draft\"],[\"Pending HOD Approval\",\"HOD\"],[\"Pending Functional Head Approval\",\"Functional Head\"],[\"Pending Head of OD and Total Rewards Approval\",\"Head of OD & Total Rewards\"],[\"Pending CAO Approval\",\"CAO\"],[\"Pending CEO Approval\",\"CEO\"]]}")
DT = CFG["dt"]
SF = CFG["sf"]
FINALS = CFG["finals"]
names = visible(DT, CFG["mode"], can_conf)
pf = [["name", "in", list(names) or NONE]]
for key in CFG["fmap"]:
    if f.get(key):
        pf.append([CFG["fmap"][key], "=", f.get(key)])
pf = date_filters(pf, f, "creation")
docs = frappe.get_all(DT, filters=pf, fields=list(set(["name", "creation", "owner", SF] + [x[0] for x in CFG["info"]])), order_by="creation desc", limit_page_length=0)
dmap = {}
for d in docs:
    dmap[d.name] = d
hist = history(DT, list(dmap.keys()), SF, dmap)
sla = flt(f.get("sla_days") or 3)
stages = CFG["stages"]
stats = {}
for s in stages:
    stats[s[0]] = {"durs": [], "pending": 0, "overdue": 0}
rows = []
for d in docs:
    h = hist[d.name]
    cur = d.get(SF) or h[-1][0]
    pending = cur not in FINALS and cur != "Draft"
    row = {"_cur": "USD", "name": d.name, "state": cur}
    for x in CFG["info"]:
        row["i_" + x[0]] = d.get(x[0])
    i = 0
    for e in h:
        end = h[i + 1][1] if i + 1 < len(h) else now
        if e[0] not in FINALS:
            dur = days(e[1], end)
            k = "s_" + e[0].lower().replace(" ", "_").replace("&", "and")
            row[k] = round((row.get(k) or 0) + dur, 1)
            if e[0] in stats and (i + 1 < len(h)):
                stats[e[0]]["durs"].append(dur)
        i += 1
    last = h[-1]
    row["entered_on"] = last[1]
    row["days_in_state"] = days(last[1], now) if cur not in FINALS else None
    row["holder"] = cur.replace("Pending ", "").replace(" Approval", "") if pending else ""
    row["overdue"] = "Yes" if pending and row["days_in_state"] > sla else ""
    endc = last[1] if cur in FINALS else now
    row["cycle_days"] = days(h[0][1], endc)
    row["last_action_by"] = last[2]
    if pending and cur in stats:
        stats[cur]["pending"] = stats[cur]["pending"] + 1
        if row["overdue"]:
            stats[cur]["overdue"] = stats[cur]["overdue"] + 1
    if f.get("pending_only") and not pending:
        continue
    if f.get("overdue_only") and not row["overdue"]:
        continue
    rows.append(row)

if f.get("view") == "Summary by Stage":
    columns = [C("stage", "Stage", "Data", None, 260), C("count", "Completed Passes", "Int", None, 130), C("avg", "Avg Days", "Float", None, 100), C("max", "Max Days", "Float", None, 100), C("pending", "Pending Now", "Int", None, 110), C("overdue", "Overdue Now (> SLA)", "Int", None, 150)]
    out = []
    for s in stages:
        ds = stats[s[0]]["durs"]
        out.append({"stage": s[1], "count": len(ds), "avg": round(sum(ds) / len(ds), 1) if ds else 0, "max": max(ds) if ds else 0, "pending": stats[s[0]]["pending"], "overdue": stats[s[0]]["overdue"]})
    chart = {"data": {"labels": [x["stage"] for x in out], "datasets": [{"name": "Avg Days", "values": [x["avg"] for x in out]}]}, "type": "bar"}
    data = columns, out, None, chart
else:
    columns = [C("name", CFG["label"], "Link", DT, 170)]
    for x in CFG["info"]:
        columns.append(C("i_" + x[0], x[1], x[2], x[3] if len(x) > 3 else None, 140))
    columns += [C("state", "Current Status", "Data", None, 190), C("holder", "Currently With", "Data", None, 160), C("entered_on", "In Status Since", "Datetime", None, 150), C("days_in_state", "Days in Status", "Float", None, 110), C("overdue", "Overdue", "Data", None, 80)]
    for s in stages:
        columns.append(C("s_" + s[0].lower().replace(" ", "_").replace("&", "and"), s[1] + " (Days)", "Float", None, 120))
    columns += [C("cycle_days", "Total Cycle (Days)", "Float", None, 120), C("last_action_by", "Last Action By", "Link", "User", 160)]
    data = columns, rows
