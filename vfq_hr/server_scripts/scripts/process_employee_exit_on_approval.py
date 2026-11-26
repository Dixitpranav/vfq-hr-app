# Server Script: Process Employee Exit on Approval
# Type: DocType Event | DocType: Employee Exit | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if doc.workflow_state == "Approved" and not doc.get("exit_processed"):
    employee = frappe.get_doc("Employee", doc.employee)
    # The employee stays Active until the formalities are closed and the HR Manager closes the exit.
    employee.db_set("custom_employee_exit", doc.name)

    formalities = [
        {"activity": "Return company assets (laptop, ID card, access cards)", "role": "IT Support"},
        {"activity": "Revoke system and email access", "role": "IT Support"},
        {"activity": "Conduct exit interview", "role": "HR Manager"},
        {"activity": "Complete knowledge transfer / handover", "role": "HOD", "assign_employee": doc.reports_to},
        {"activity": "Process final settlement and full and final payment", "role": "HR Manager"},
        {"activity": "Update payroll and benefits records", "role": "HR Manager"},
    ]

    exit_assign_failures = []
    doc.set("activities", [])
    for item in formalities:
        task = frappe.get_doc({
            "doctype": "Task",
            "subject": item["activity"] + " - " + doc.employee_name,
            "status": "Open",
            "priority": "Medium",
            "exp_end_date": doc.last_working_day,
            "description": "Exit formality for " + doc.employee_name + " (" + doc.employee + ")",
            "custom_employee_exit": doc.name
        })
        task.insert(ignore_permissions=True)

        assign_users = []
        specific_emp = item.get("assign_employee")
        if specific_emp:
            user_id = frappe.db.get_value("Employee", specific_emp, "user_id")
            if user_id:
                assign_users = [user_id]
            else:
                exit_assign_failures.append(item["activity"] + ": " + str(specific_emp) + " has no linked user, so the task went to everyone with the " + item["role"] + " role")
        if not assign_users:
            role_users = frappe.get_all("Has Role", filters={"role": item["role"], "parenttype": "User"}, pluck="parent")
            # only real, enabled people: skip Administrator/Guest, disabled users and the AI agent accounts
            enabled_users = frappe.get_all("User", filters={"name": ["in", role_users], "enabled": 1}, pluck="name")
            assign_users = [u for u in enabled_users if u not in ("Administrator", "Guest") and not u.endswith("@ai-agents.invalid")]
            if not assign_users:
                exit_assign_failures.append(item["activity"] + ": no enabled user holds the " + item["role"] + " role")
        if assign_users:
            try:
                frappe.call(
                    "frappe.desk.form.assign_to.add",
                    doctype="Task",
                    name=task.name,
                    assign_to=assign_users,
                    description=item["activity"] + " for " + doc.employee_name
                )
            except Exception as err:
                frappe.log_error(title="Exit task assignment failed", message=frappe.get_traceback())
                exit_assign_failures.append(item["activity"] + ": " + str(err))

        doc.append("activities", {
            "activity": item["activity"],
            "role": item["role"],
            "status": "Pending",
            "task": task.name
        })

    doc.offboarding_status = "Approved & Pending Tasks"
    doc.exit_processed = 1
    if exit_assign_failures:
        frappe.msgprint(
            "The exit was processed, but these tasks were created without an assignee and need to be assigned manually:<br>" + "<br>".join(exit_assign_failures),
            title="Some Exit Tasks Not Assigned",
            indicator="orange"
        )

# Final step: HR Manager closes the exit. Only now does the employee become Left.
if doc.workflow_state == "Exit Closed":
    open_exit_tasks = frappe.get_all(
        "Task",
        filters={"custom_employee_exit": doc.name, "status": ["not in", ["Completed", "Cancelled"]]},
        pluck="subject",
    )
    if open_exit_tasks:
        frappe.throw(
            "The exit cannot be closed yet. These exit formalities are still open:<br>" + "<br>".join(open_exit_tasks) + "<br><br>Close each task, then close the exit again.",
            title="Exit Formalities Still Open"
        )
    if not doc.get("exit_processed"):
        frappe.throw("This exit has not been through manager and HR approval yet, so it cannot be closed.", title="Exit Not Approved")
    closing_employee = frappe.get_doc("Employee", doc.employee)
    closing_employee.db_set("status", "Left")
    closing_employee.db_set("relieving_date", doc.last_working_day)
    closing_employee.db_set("custom_employee_exit", doc.name)
    if doc.exit_reason:
        closing_employee.db_set("reason_for_leaving", doc.exit_reason)
