# Server Script: Annual Performance Review - Require Completed Mid-Year
# Type: DocType Event | DocType: Annual Performance Review | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# An Annual Performance Review needs a Completed Mid-Year Review (H1 or H2) for the same year.
# Checked when the Annual Review is created and whenever it moves to another workflow stage.
def run_script(doc):
    if doc.flags.ignore_permissions or not doc.employee or not doc.review_year:
        return
    if not doc.is_new():
        before = doc.get_doc_before_save()
        if before and (before.workflow_state or "") == (doc.workflow_state or ""):
            return
    year = str(frappe.utils.cint(doc.review_year))
    if frappe.db.exists("Mid-Year Review", {"employee": doc.employee, "review_year": year, "workflow_state": "Completed"}):
        return
    who = doc.get("employee_name") or doc.employee
    frappe.throw(
        f"{who} does not have a Completed Mid-Year Review for {year}. Complete the {year} Mid-Year Review (H1 or H2) before creating or progressing the Annual Performance Review.",
        title="Mid-Year Review Required",
    )

run_script(doc)
