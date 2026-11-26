// Client Script: Employee Exit - Reason List (Employee Exit, Form)
frappe.ui.form.on("Employee Exit", {
    setup(frm) {
        frm.set_query("custom_exit_reason", function () {
            const f = {enabled: 1};
            if (frm.doc.exit_type) { f.exit_type = frm.doc.exit_type; }
            return {filters: f};
        });
    },
    refresh(frm) {
        const mgr = ["HOD", "HR Manager", "System Manager", "Reporting Manager", "Line Manager"];
        const can = frappe.session.user === "Administrator" || (frappe.user_roles || []).some(r => mgr.includes(r)) || !frm.doc.workflow_state || frm.doc.workflow_state === "Draft";
        frm.set_df_property("custom_exit_reason", "read_only", can ? 0 : 1);
        if (!can) {
            frm.set_df_property("custom_exit_reason", "description", "Chosen when the resignation was submitted. Your manager or HR can update it; add details in Additional Comments.");
        }
    },
    exit_type(frm) {
        if (frm.doc.custom_exit_reason) { frm.set_value("custom_exit_reason", ""); }
    }
});

// Guidance banner for each stage of the resignation.
frappe.ui.form.on("Employee Exit", {
    refresh(frm) {
        if (frm.is_new()) return;
        const st = frm.doc.workflow_state || "Draft";
        const msg = {
            "Draft": "Check your Resignation Date and Last Working Day, choose a Reason for Leaving, then click <b>Actions &rsaquo; Submit Resignation</b>. A signed acknowledgement PDF is attached automatically.",
            "Pending Manager Approval": "Submitted. Waiting for your manager's approval.",
            "Pending HR Approval": "Approved by the manager. Waiting for HR approval.",
            "Approved": "Resignation approved. The signed acknowledgement is attached under Resignation Documents.",
            "Rejected": "This resignation was not approved. Contact HR if you have questions.",
            "Exit Closed": "Exit completed and closed."
        }[st];
        if (msg) frm.set_intro(msg, st === "Rejected" ? "red" : (st === "Approved" || st === "Exit Closed" ? "green" : "blue"));
    }
});
