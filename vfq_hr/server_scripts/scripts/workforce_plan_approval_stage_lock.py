# Server Script: Workforce Plan - Approval Stage Lock
# Type: DocType Event | DocType: Workforce Plan | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
if before:
    old_state = before.workflow_state or ""
    new_state = doc.workflow_state or ""
    if old_state.startswith("Pending "):
        if old_state == new_state and frappe.session.user != "Administrator":
            frappe.throw("This Workforce Plan is in approval and cannot be edited. The creator can use Actions > Request Send Back for Review.", title="Plan Locked During Approval")
        if old_state != new_state and before.get("custom_send_back_requested"):
            if new_state not in ("Draft", "Rejected"):
                frappe.throw("The creator has requested this plan back for review. Use Send Back for Review or Reject instead of Approve.", title="Send Back Requested")
            doc.custom_send_back_requested = 0
            doc.custom_send_back_reason = None
            doc.custom_send_back_requested_by = None
            doc.custom_send_back_requested_on = None
