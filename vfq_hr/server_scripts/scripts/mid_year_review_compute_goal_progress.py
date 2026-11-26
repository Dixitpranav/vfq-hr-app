# Server Script: Mid-Year Review - Compute Goal Progress
# Type: DocType Event | DocType: Mid-Year Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Progress % is worked out in the browser; compute it here too so API / import entries never fail with "Value missing for Progress %".
for goal_row in (doc.get("mid_year_review_goal") or []):
    if goal_row.progress_ in (None, ""):
        goal_target = frappe.utils.flt(goal_row.target)
        if goal_target > 0:
            goal_row.progress_ = (frappe.utils.flt(goal_row.achievement) / goal_target) * 100
        else:
            frappe.throw(
                "Goal row " + str(goal_row.idx) + " (" + str(goal_row.goal) + ") needs a Target above 0 so Progress % can be worked out.",
                title="Target Required"
            )
