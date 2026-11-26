// Client Script: Job Requisition - Gate Manual Create Job Opening Button (Job Requisition, Form)
frappe.ui.form.on('Job Requisition', {
    refresh: function(frm) {
        if (frm.is_new()) return;
        var is_approved = frm.doc.workflow_state === 'Approved';
        frappe.db.count('Job Opening', {filters: {job_requisition: frm.doc.name}}).then(function(count) {
            if (!is_approved || count > 0) {
                frm.remove_custom_button('Create Job Opening', 'Actions');
            }
        });
    }
});
