# Server Script: Mid-Year Review - Required Fields by Stage
# Type: DocType Event | DocType: Mid-Year Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
if before and before.workflow_state != doc.workflow_state:
    missing = []
    if doc.workflow_state == "Employee Acknowledgement":
        for f, label in [("manager_feedback", "Manager Feedback"), ("strengths", "Strengths"), ("areas_of_improvement", "Areas of Improvement"), ("training_recommendations", "Training Recommendations"), ("action_plan", "Action Plan")]:
            if not doc.get(f):
                missing.append(label)
        for r in (doc.get("mid_year_review_goal") or []):
            if not r.manager_comments:
                missing.append("Manager Comments on goal row " + str(r.idx))
    if doc.workflow_state == "Completed" and not doc.get("employee_feedback"):
        missing.append("Employee Feedback")
    if missing:
        frappe.throw("Complete these before moving to " + doc.workflow_state + ": " + ", ".join(missing), title="Required Fields")
