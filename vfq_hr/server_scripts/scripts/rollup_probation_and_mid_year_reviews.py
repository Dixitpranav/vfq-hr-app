# Server Script: Rollup Probation and Mid-Year Reviews
# Type: DocType Event | DocType: Annual Performance Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.employee:
    doc.set("linked_probation_reviews", [])
    probation_reviews = frappe.get_all(
        "Probation Review",
        filters={"employee": doc.employee, "docstatus": 1},
        fields=["name", "review_date", "probation_end_date", "decision", "overall_rating"],
        order_by="review_date desc",
    )
    for pr in probation_reviews:
        doc.append("linked_probation_reviews", {
            "probation_review": pr.name,
            "review_date": pr.review_date,
            "probation_end_date": pr.probation_end_date,
            "decision": pr.decision,
            "overall_rating": pr.overall_rating,
        })

    doc.set("linked_mid_year_reviews", [])
    mid_year_reviews = frappe.get_all(
        "Mid-Year Review",
        filters={"employee": doc.employee, "workflow_state": "Completed"},
        fields=["name", "review_period", "review_year", "overall_assessment"],
        order_by="review_year desc, review_period desc",
    )
    for mr in mid_year_reviews:
        doc.append("linked_mid_year_reviews", {
            "mid_year_review": mr.name,
            "review_period": mr.review_period,
            "review_year": mr.review_year,
            "overall_assessment": mr.overall_assessment,
        })
