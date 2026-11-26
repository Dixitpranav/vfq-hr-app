# Server Script: Employee Exit - Reopen Position on Close
# Type: DocType Event | DocType: Employee Exit | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
if doc.workflow_state == "Exit Closed" and before and before.workflow_state != "Exit Closed" and not doc.get("custom_position_released"):
    flt = frappe.utils.flt
    plan_name = frappe.db.get_value("Employee", doc.employee, "custom_budget_plan")
    if plan_name:
        plan = frappe.get_doc("Workforce Plan", plan_name)
        if plan.docstatus == 1 and flt(plan.consumed_headcount) > 0:
            consumed_hc = flt(plan.consumed_headcount) - 1
            remaining_hc = flt(plan.approved_headcount) - flt(plan.committed_headcount) - consumed_hc
            plan.db_set("consumed_headcount", consumed_hc)
            plan.db_set("remaining_headcount", remaining_hc)
            plan.db_set("custom_positions_summary", str(int(consumed_hc)) + " filled / " + str(int(max(remaining_hc, 0))) + " open / " + str(int(flt(plan.approved_headcount))) + " approved")
    doc.db_set("custom_position_released", 1)
