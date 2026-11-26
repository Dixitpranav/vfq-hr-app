// Client Script: Disable Status field from job Req (Job Requisition, Form)
frappe.ui.form.on('Job Requisition', {
    refresh(frm) {
        if (frm.fields_dict.status) {
            frm.toggle_display('status', false);
        }
    }
});
