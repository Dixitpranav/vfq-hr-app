# Server Script: Leave Application - Ensure Approval Flow Is Set
# Type: DocType Event | DocType: Leave Application | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Make sure the approval flow is always set (the form sets it in the browser; API/imports did not),
# otherwise the workflow shows only Reject and the user is stuck without an explanation.
if doc.leave_type and not doc.custom_approval_flow:
    flow_value = frappe.db.get_value("Leave Type", doc.leave_type, "custom_approval_flow")
    if not flow_value:
        frappe.throw(
            "Leave Type " + str(doc.leave_type) + " has no Approval Flow (Single-Layer or Multi-Layer). Open the Leave Type, set Approval Flow, save, and then submit this leave.",
            title="Approval Flow Missing"
        )
    doc.custom_approval_flow = flow_value
