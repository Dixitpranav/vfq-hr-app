# Server Script: Sync Exit Task Completion to Activity
# Type: DocType Event | DocType: Task | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.get("custom_employee_exit"):
    activity_row = frappe.db.get_value(
        "Employee Exit Activity",
        {"task": doc.name},
        ["name", "parent", "activity"],
        as_dict=True
    )
    if activity_row:
        new_status = "Completed" if doc.status == "Completed" else "Pending"
        frappe.db.set_value("Employee Exit Activity", activity_row.name, "status", new_status)

        activities = frappe.get_all(
            "Employee Exit Activity",
            filters={"parent": activity_row.parent},
            fields=["activity", "status"]
        )
        done = set(a.activity for a in activities if a.status == "Completed")

        checkbox_map = {
            "assets_returned": set(["Return company assets (laptop, ID card, access cards)"]),
            "access_revoked": set(["Revoke system and email access"]),
            "exit_interview_done": set(["Conduct exit interview"]),
            "final_settlement_done": set([
                "Process final settlement and full and final payment",
                "Update payroll and benefits records",
            ]),
        }
        for field, required in checkbox_map.items():
            frappe.db.set_value("Employee Exit", activity_row.parent, field, 1 if required.issubset(done) else 0)

        all_activities_done = len(activities) > 0 and all(a.status == "Completed" for a in activities)
        new_offboarding_status = "Completed" if all_activities_done else "Approved & Pending Tasks"
        frappe.db.set_value("Employee Exit", activity_row.parent, "offboarding_status", new_offboarding_status)
