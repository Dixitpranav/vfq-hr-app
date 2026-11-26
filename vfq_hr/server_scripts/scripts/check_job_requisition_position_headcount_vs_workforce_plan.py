# Server Script: Check Job Requisition Position Headcount vs Workforce Plan
# Type: DocType Event | DocType: Job Requisition | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Soft, non-blocking check: warns (does not block) when a Job Requisition Role row's
# headcount would push a Workforce Plan position's total reservations (across ALL
# Job Requisitions referencing that plan, Draft or submitted, excluding Rejected/
# Cancelled ones) beyond that position's approved Role Count. A position counts as
# "reserved" by a requisition as soon as that requisition is created (even Draft),
# not only once it is submitted/approved.
#
# This never blocks save or submit. If the user proceeds anyway, each row's own
# headcount_over_plan field records the overage as a visible, queryable variance
# flag, recomputed fresh on every save of THIS requisition.

warnings = []

for row in (doc.get('custom_roles') or []):
    wp_pos = row.get('workforce_plan_position')
    if not wp_pos or not row.get('no_of_positions'):
        row.headcount_over_plan = 0
        continue

    approved = frappe.db.get_value('Workforce Plan Position', wp_pos, 'role_count') or 0

    other_rows = frappe.get_all(
        'Job Requisition Role',
        filters={'workforce_plan_position': wp_pos, 'parent': ['!=', doc.name]},
        fields=['parent', 'no_of_positions'],
    )

    parent_names = []
    for r in other_rows:
        if r.parent not in parent_names:
            parent_names.append(r.parent)

    active_parents = []
    if parent_names:
        active_parents = frappe.get_all(
            'Job Requisition',
            filters={'name': ['in', parent_names], 'workflow_state': ['!=', 'Rejected'], 'docstatus': ['!=', 2]},
            pluck='name',
        )

    other_reserved = 0
    holding_reqs = []
    for r in other_rows:
        if r.parent in active_parents:
            other_reserved += (r.no_of_positions or 0)
            if (r.no_of_positions or 0) > 0 and r.parent not in holding_reqs:
                holding_reqs.append(r.parent)
    holding_reqs.sort()

    total_after = other_reserved + (row.no_of_positions or 0)
    overage = total_after - approved
    if overage < 0:
        overage = 0
    row.headcount_over_plan = overage

    if overage > 0:
        position_label = row.get('designation') or wp_pos
        if holding_reqs:
            held_by = ', '.join(frappe.bold(h) for h in holding_reqs)
            warnings.append(
                f"{frappe.bold(position_label)}: approved headcount is {approved}, already reserved by {held_by} ({other_reserved} of it). This row adds {row.no_of_positions}, exceeding the Workforce Plan's approved count by {overage}."
            )
        else:
            warnings.append(
                f"{frappe.bold(position_label)}: approved headcount is {approved}, this row alone requests {row.no_of_positions}, exceeding it by {overage}."
            )

if warnings:
    frappe.msgprint(
        "This Job Requisition exceeds the Workforce Plan's approved headcount for one or more positions:<br><br>"
        + "<br><br>".join(warnings)
        + "<br><br>You can still save/submit -- this is a warning, not a block. The excess is recorded as a variance on each affected row.",
        title="Headcount Exceeds Workforce Plan",
        indicator="orange",
    )
