# Server Script: CXO Hiring Approval - Log Send Back Reason
# Type: DocType Event | DocType: CXO Hiring Approval | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
if before and before.workflow_state != doc.workflow_state:
    if before.workflow_state in ("Pending Head of OD Approval", "Pending CHRO Approval", "Pending CAO Approval", "Pending CEO Approval") and doc.workflow_state == "Draft":
        reason = (doc.get("custom_send_back_reason") or "").strip()
        if len(reason) < 10:
            frappe.throw("Enter the reason for sending this batch back for review.", title="Reason Required")
        stage = {"Pending Head of OD Approval": "Head of OD", "Pending CHRO Approval": "CHRO", "Pending CAO Approval": "CAO"}.get(before.workflow_state, "CEO")
        sender = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
        safe_reason = reason.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        doc.add_comment("Comment", "<b>Sent back for review by " + stage + "</b> (" + sender + ").<br>Reason: " + safe_reason)
        doc.cao_approved_by = None
        doc.cao_approved_on = None
        doc.ceo_approved_by = None
        doc.ceo_approved_on = None
        doc.custom_hod_approved_by = None
        doc.custom_hod_approved_on = None
        doc.custom_chro_approved_by = None
        doc.custom_chro_approved_on = None
    doc.custom_send_back_reason = None
