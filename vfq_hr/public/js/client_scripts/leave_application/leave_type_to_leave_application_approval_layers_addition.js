// Client Script: Leave Type to Leave Application Approval layers addition (Leave Application, Form)
frappe.ui.form.on("Leave Application", {
    leave_type(frm) {

        if (!frm.doc.leave_type) return;

        frappe.db.get_value(
            "Leave Type",
            frm.doc.leave_type,
            "custom_approval_flow"
        ).then(r => {

            frm.set_value(
                "custom_approval_flow",
                r.message.custom_approval_flow
            );

        });

    }
});
