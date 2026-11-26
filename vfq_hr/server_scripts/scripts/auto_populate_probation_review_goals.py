# Server Script: Auto-Populate Probation Review Goals
# Type: DocType Event | DocType: Probation Review | Event: Before Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if not doc.get("goals"):
    default_goals = [
        "Understand role responsibilities and key deliverables",
        "Complete required onboarding and product/process training",
        "Deliver assigned tasks meeting quality and timeline expectations",
    ]
    for goal_text in default_goals:
        doc.append("goals", {
            "goal": goal_text,
        })
