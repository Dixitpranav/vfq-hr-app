# Server Script: CXO Hiring Approval - Approval Remarks Stage Lock
# Type: DocType Event | DocType: CXO Hiring Approval | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# CAO Remarks can only be changed by a CAO at Pending CAO Approval.
# CEO Remarks can only be changed by a CEO at Pending CEO Approval.
def_user = frappe.session.user
if def_user != "Administrator":
    before = doc.get_doc_before_save()
    old_state = before.workflow_state if before else ""
    old_cao = (before.get("cao_remarks") if before else "") or ""
    old_ceo = (before.get("ceo_remarks") if before else "") or ""
    if (doc.get("cao_remarks") or "") != old_cao:
        is_cao = frappe.db.exists("Has Role", {"parent": def_user, "parenttype": "User", "role": "CAO"})
        if old_state != "Pending CAO Approval" or not is_cao:
            frappe.throw("CAO Remarks can only be edited by the CAO while the batch is at Pending CAO Approval.", title="Remarks Locked")
    if (doc.get("ceo_remarks") or "") != old_ceo:
        is_ceo = frappe.db.exists("Has Role", {"parent": def_user, "parenttype": "User", "role": "CEO / Final Approver"})
        if old_state != "Pending CEO Approval" or not is_ceo:
            frappe.throw("CEO Remarks can only be edited by the CEO while the batch is at Pending CEO Approval.", title="Remarks Locked")

# Head of OD Remarks and CHRO Remarks follow the same rule at their own stage.
if frappe.session.user != "Administrator":
    prev = doc.get_doc_before_save()
    prev_state = prev.workflow_state if prev else ""
    stage_rules = [
        ["custom_hod_remarks", "Pending Head of OD Approval", "Head of OD & Total Rewards", "Head of OD"],
        ["custom_chro_remarks", "Pending CHRO Approval", "CHRO", "CHRO"],
    ]
    for rule in stage_rules:
        old_val = (prev.get(rule[0]) if prev else "") or ""
        if (doc.get(rule[0]) or "") != old_val:
            has_role = frappe.db.exists("Has Role", {"parent": frappe.session.user, "parenttype": "User", "role": rule[2]})
            if prev_state != rule[1] or not has_role:
                frappe.throw(rule[3] + " Remarks can only be edited by the " + rule[3] + " while the batch is at " + rule[1] + ".", title="Remarks Locked")
