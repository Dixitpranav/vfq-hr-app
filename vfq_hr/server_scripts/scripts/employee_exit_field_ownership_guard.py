# Server Script: Employee Exit - Field Ownership Guard
# Type: DocType Event | DocType: Employee Exit | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Field ownership: the employee edits only their own part, the employee's Reports To edits the
# manager part, HR (HR User / HR Manager, never on their own record) edits the HR and manager parts.
# System Manager and Administrator are not restricted.
def run_script(doc):
    cfg = {"emp_states":["Draft"],"emp":["exit_type","custom_exit_reason","exit_reason","notice_date","custom_signed_resignation","knowledge_transfer_notes"],"mgr":["custom_exit_reason","knowledge_transfer_notes"],"hr":["employee","rehire_eligible","custom_signed_acceptance","hr_approver","exit_interview_notes"],"tables":{"activities":{"emp":[],"mgr":[],"hr":["status","remarks"],"self_only":1}}}
    if doc.is_new():
        return
    user = frappe.session.user
    if user == "Administrator":
        return
    roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
    if "System Manager" in roles:
        return
    before = doc.get_doc_before_save()
    if not before:
        return

    def norm(v):
        if v is None:
            return ""
        if isinstance(v, bool):
            v = int(v)
        if isinstance(v, (int, float)):
            if float(v) == 0:
                return ""
            return str(round(float(v), 6))
        return str(v).replace("\r\n", "\n").strip()

    me = frappe.db.get_value("Employee", {"user_id": user}, "name")
    subject = doc.get("employee") or before.get("employee")
    is_self = bool(me) and me == subject
    boss = frappe.db.get_value("Employee", subject, "reports_to") if subject else None
    is_mgr = bool(me) and bool(boss) and boss == me and not is_self
    is_hr = (not is_self) and ("HR User" in roles or "HR Manager" in roles)
    state = before.get("workflow_state") or "Draft"
    emp_ok = is_self and state in cfg["emp_states"]

    can = set()
    if emp_ok:
        can.update(cfg["emp"])
    if is_mgr or is_hr:
        can.update(cfg["mgr"])
    if is_hr:
        can.update(cfg["hr"])

    blocked = []
    for f in set(cfg["emp"] + cfg["mgr"] + cfg["hr"]):
        if f not in can and norm(doc.get(f)) != norm(before.get(f)):
            blocked.append(doc.meta.get_label(f) or f)

    for tf in cfg["tables"]:
        tcfg = cfg["tables"][tf]
        if tcfg["self_only"] and not is_self:
            continue
        tcan = set()
        if emp_ok:
            tcan.update(tcfg["emp"])
        if is_mgr or is_hr:
            tcan.update(tcfg["mgr"])
        if is_hr:
            tcan.update(tcfg["hr"])
        tlabel = doc.meta.get_label(tf) or tf
        old_rows = {}
        for r in (before.get(tf) or []):
            old_rows[r.name] = r
        kept = []
        for r in (doc.get(tf) or []):
            o = old_rows.get(r.name) if r.name else None
            if not o:
                if not is_hr:
                    blocked.append(tlabel + " (adding rows)")
                continue
            kept.append(r.name)
            for f in set(tcfg["emp"] + tcfg["mgr"] + tcfg["hr"]):
                if f not in tcan and norm(r.get(f)) != norm(o.get(f)):
                    blocked.append(tlabel + " row " + str(r.idx) + ": " + (r.meta.get_label(f) or f))
        for n in old_rows:
            if n not in kept and not is_hr:
                blocked.append(tlabel + " (removing rows)")

    if blocked:
        uniq = []
        for b in blocked:
            if b not in uniq:
                uniq.append(b)
        if is_self:
            who = "As the employee on this record you can only fill in your own part" + ("" if emp_ok else " and only while it is at your stage") + "."
        elif is_mgr:
            who = "As the Reports To manager you can only fill in the manager part."
        elif is_hr:
            who = "As HR you can fill in the HR and manager parts, but not the employee's own part."
        else:
            who = "Only the employee, their Reports To manager or HR can change this record, each for their own part."
        frappe.throw(who + " These fields belong to someone else or are locked at this stage: " + ", ".join(uniq) + ". Undo these changes and save again.", title="Not Your Part to Edit")

run_script(doc)
