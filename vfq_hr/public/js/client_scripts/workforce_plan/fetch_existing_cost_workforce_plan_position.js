// Client Script: Fetch Existing Cost - Workforce Plan Position (Workforce Plan, Form)
frappe.ui.form.on("Workforce Plan Position", {
    fetch_existing_cost_btn(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (frm.doc.docstatus !== 0) {
            frappe.msgprint({title: "Not allowed", message: "This Workforce Plan is already submitted, so Existing Cost can no longer be changed.", indicator: "red"});
            return;
        }
        if (row.role_type !== "Existing Role") {
            frappe.msgprint("Fetch Existing Cost only applies to Existing Role positions.");
            return;
        }
        frappe.call({
            method: "fetch_existing_cost_for_role",
            args: { designation: row.position, sub_function: row.sub_function },
            callback: function (r) {
                if (!r.message) return;
                if (!r.message.found) {
                    frappe.show_alert({
                        message: "No onboarding history found for this role. Your current Existing Cost was kept - enter it manually if needed.",
                        indicator: "orange"
                    });
                    return;
                }
                frappe.model.set_value(cdt, cdn, "existing_cost_usd", r.message.existing_cost_usd);
                frappe.model.set_value(cdt, cdn, "existing_cost_source_summary", r.message.summary);
                frm.refresh_field("positions");
                frappe.show_alert({message: "Existing Cost fetched from onboarding history.", indicator: "green"});
            }
        });
    }
});
