# Server Script: Mid-Year Review - Require Probation Confirmation
# Type: DocType Event | DocType: Mid-Year Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.employee and doc.get("workflow_state") and doc.workflow_state != "Draft":
    confirmation_status = frappe.db.get_value("Employee", doc.employee, "custom_confirmation_status")
    if confirmation_status in ("Probation", "Extended", "Terminated"):
        who = doc.employee_name or doc.employee
        message = "Cannot progress this " + doc.doctype + " for " + who + ": their Probation Review has not reached a Confirmed decision yet (current confirmation status: " + confirmation_status + "). Complete and confirm the Probation Review before submitting Mid-Year or Annual performance reviews."
        if confirmation_status == "Extended":
            open_reviews = frappe.get_all("Probation Review", filters={"employee": doc.employee, "docstatus": 0}, fields=["name", "workflow_state", "probation_end_date"], order_by="creation desc", limit=1)
            if open_reviews:
                review = open_reviews[0]
                link = '<a href="/app/probation-review/' + review.name + '"><b>' + review.name + '</b></a>'
                message = "Probation for " + who + " was extended to " + frappe.utils.formatdate(review.probation_end_date) + ". The follow-up Probation Review " + link + " is still at " + review.workflow_state + ". Complete that review with the decision Confirm, then submit this " + doc.doctype + "."
        frappe.throw(message, title="Probation Not Confirmed")
