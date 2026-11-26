# Server Script: Submit Portal Resignation
# Type: API | API method: submit_portal_resignation
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Explicit submit action for the portal resignation flow ("/resignation" web form).
# Called only when the employee clicks the "Submit Resignation Request" button that the
# web form's client script shows once the signed letter is attached. This is the one and
# only way a Draft portal resignation moves to "Pending Manager Approval" -- simply saving
# the record with the file attached no longer auto-submits it (see Employee Exit - Auto
# Submit Portal Resignation, now disabled).
#
# Params (frappe.form_dict): name (Employee Exit name)
# Response: {submitted, message}

name = frappe.form_dict.get("name")
if not name:
    frappe.throw("Resignation name is required.")

doc = frappe.get_doc("Employee Exit", name)

emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
if not emp or emp != doc.employee:
    frappe.throw("You are not allowed to submit this resignation.")

if doc.exit_type != "Resignation":
    frappe.throw("This action is only available for resignations.")

if doc.get("workflow_state") not in (None, "", "Draft"):
    frappe.response["message"] = {"submitted": False, "message": "This request has already been submitted."}
else:
    # Signed letter upload is optional; the system attaches a signed acknowledgement automatically.
    if not doc.get("custom_exit_reason"):
        frappe.throw("Please choose a Reason for Leaving before submitting.")
    frappe.call("frappe.model.workflow.apply_workflow", doc=doc, action="Submit Resignation")
    frappe.response["message"] = {"submitted": True, "message": "Your resignation has been submitted to your manager."}
