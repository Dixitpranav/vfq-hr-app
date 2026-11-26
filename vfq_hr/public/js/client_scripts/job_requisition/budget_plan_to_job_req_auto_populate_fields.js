// Client Script: Budget plan to Job req auto populate fields (Job Requisition, Form)
frappe.ui.form.on("Job Requisition", {
    refresh(frm) {
        // Scope the Designation picker on each Roles row to only the positions
        // listed in the selected Workforce Plan, so users can't even pick an
        // out-of-plan position from the UI (server-side check backs this up --
        // see Server Script "Restrict Job Requisition Roles to Workforce Plan
        // Positions").
        frm.set_query("designation", "custom_roles", function () {
            if (frm.doc.custom_budget_plan && frm.__wp_allowed_designations && frm.__wp_allowed_designations.length) {
                return { filters: { name: ["in", frm.__wp_allowed_designations] } };
            }
            return {};
        });
        if (frm.doc.custom_budget_plan && !frm.__wp_allowed_designations) {
            frappe.db.get_doc("Workforce Plan", frm.doc.custom_budget_plan).then(doc => {
                frm.__wp_allowed_designations = (doc.positions || []).map(p => p.position).filter(Boolean);
            });
        }
    },
    custom_budget_plan(frm) {
        if (!frm.doc.custom_budget_plan) return;
        frappe.db.get_doc(
            "Workforce Plan",
            frm.doc.custom_budget_plan
        ).then(doc => {
            frm.set_value("company", doc.custom_company);
            frm.set_value("custom_cost_center", doc.cost_center);
            frm.set_value("custom_budget_line", doc.budget_line);
            frm.set_value("custom_approved_budget", doc.total_budget_impact);
            frm.set_value("custom_consumed_budget", doc.consumed_budget);
            frm.set_value(
                "custom_remaining_budget",
                (doc.total_budget_impact || 0) - (doc.committed_budget || 0) - (doc.consumed_budget || 0)
            );
            frm.set_value("custom_approved_headcount", doc.approved_headcount);
            frm.set_value("custom_consumed_headcount", doc.consumed_headcount);
            frm.set_value(
                "custom_remaining_headcount",
                (doc.approved_headcount || 0) - (doc.committed_headcount || 0) - (doc.consumed_headcount || 0)
            );
            // Informational only -- a point-in-time snapshot taken when the budget
            // plan is selected. The real check at approval time re-fetches the
            // Workforce Plan live, so this on-screen value can drift if other
            // requisitions consume budget before this one is approved.

            // Cache the allowed-designations list for the Designation query filter
            // above (refresh handler), so it reflects the newly chosen plan right away.
            frm.__wp_allowed_designations = (doc.positions || []).map(p => p.position).filter(Boolean);

            // Push the Workforce Plan's positions into the Job Requisition Role
            // child table, one row per position, REPLACING whatever rows are
            // already there. This runs every time the Workforce Plan is chosen
            // or changed (confirmed behaviour, approved by the user).
            // Vendor, Project, Location, Hiring Remarks, Role Classification and
            // Current Entity Status have no equivalent on Workforce Plan Position
            // (or, for Current Entity Status, use incompatible value sets), so
            // they are intentionally left blank as pending fields for the user
            // to fill in per row.
            frm.clear_table("custom_roles");
            (doc.positions || []).forEach(pos => {
                const row = frm.add_child("custom_roles");
                row.designation = pos.position;
                row.role_title = pos.position;
        row.custom_employment_type = pos.custom_employment_type;
                row.role_classification = pos.role_classification;
            row.role_code = pos.role_code;
                row.sub_function = pos.sub_function;
                row.project = doc.custom_project;
                row.workforce_plan_position = pos.name;
                row.no_of_positions = pos.role_count;
                row.role_type = (pos.role_type === "Replacement Role") ? "Replacement" : pos.role_type;
                row.experience_required = pos.experience_required;
                row.expertise_skillset = pos.expertise_required;
                row.scope = pos.scope;
                row.business_critical_info = pos.critical_info;
                row.additional_hardware = pos.additional_hardware;
                row.role_description = pos.role_description;
                row.custom_function = pos.function;
                row.custom_sub_function = pos.custom_sub_function;
                row.hiring_manager = pos.hiring_manager;
                if (pos.role_type === "New Role") {
                    row.estimated_cost_usd = pos.existing_cost_usd;
                    // Existing Cost intentionally left blank so the save-time
                    // "JR Role Rollup" script's own hiring-history auto-estimate
                    // can still try to fill it in, as it already does today.
                } else {
                    // Existing Role: Workforce Plan has no separate "new hire"
                    // estimate distinct from the incumbent's current cost, and
                    // Estimated Cost (USD) is mandatory on every row -- so both
                    // fields get the same known figure instead of leaving
                    // Estimated Cost blank and failing to save.
                    row.existing_cost_usd = pos.existing_cost_usd;
                    row.estimated_cost_usd = pos.existing_cost_usd;
                }
            });
            frm.refresh_field("custom_roles");
        });
    }
});


frappe.ui.form.on("Job Requisition Role", {
    fetch_existing_cost_btn(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (frm.doc.workflow_state && !["Draft","Pending HR Manager Approval"].includes(frm.doc.workflow_state)) {
            frappe.msgprint({title: "Not allowed", message: "This requisition is already past approval, so Existing Cost can no longer be changed.", indicator: "red"});
            return;
        }
        if (row.role_type !== "Existing Role" && row.role_type !== "Replacement") {
            frappe.msgprint("Fetch Existing Cost only applies to Existing Role or Replacement rows.");
            return;
        }
        frappe.call({
            method: "fetch_existing_cost_for_role",
            args: { designation: row.designation, sub_function: row.sub_function },
            callback: function (r) {
                if (!r.message) return;
                if (!r.message.found) {
                    frappe.show_alert({message: "No onboarding history found for this role. Your current Existing Cost was kept - enter it manually if needed.", indicator: "orange"});
                    return;
                }
                frappe.model.set_value(cdt, cdn, "existing_cost_usd", r.message.existing_cost_usd);
                frappe.model.set_value(cdt, cdn, "existing_cost_source_summary", r.message.summary);
                frm.refresh_field("custom_roles");

                // Also push the freshly fetched value back onto the linked Workforce Plan
                // Position, so the plan stays in sync with what was just re-fetched here.
                if (row.workforce_plan_position) {
                    frappe.call({
                        method: "frappe.client.set_value",
                        args: {
                            doctype: "Workforce Plan Position",
                            name: row.workforce_plan_position,
                            fieldname: {
                                existing_cost_usd: r.message.existing_cost_usd,
                                existing_cost_source_summary: r.message.summary
                            }
                        }
                    });
                }

                frappe.show_alert({
                    message: r.message.found
                        ? "Existing Cost re-fetched and pushed to the linked Workforce Plan."
                        : "No onboarding history found yet -- see the explanation below the field.",
                    indicator: r.message.found ? "green" : "orange"
                });
            }
        });
    }
});


frappe.ui.form.on("Job Requisition", {
    refresh: function(frm) {
        // Only submitted Budgets may be picked as the Budget Line; scope by the plan's own Cost Center when known.
        frm.set_query("custom_budget_line", function() {
            var filters = {docstatus: 1};
            if (frm.doc.custom_cost_center) {
                filters.cost_center = frm.doc.custom_cost_center;
            }
            return {filters: filters};
        });
    }
});
