// Client Script: CXO Hiring Approval - Live Shortlisted Count (CXO Hiring Approval, Form)
// Shows how many Shortlisted applicants a Function will add as soon as the Function is chosen.
// The applicants and approval rows themselves are added when the form is saved.
function cxo_load_shortlisted_count(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    if (!row.function) {
        frappe.model.set_value(cdt, cdn, 'shortlisted_count', 0);
        return;
    }
    frappe.call({
        method: 'get_cxo_function_shortlist',
        args: { function: row.function, current: frm.is_new() ? '' : frm.doc.name },
        callback: function(r) {
            if (!r.message) return;
            frappe.model.set_value(cdt, cdn, 'shortlisted_count', r.message.count);
            if (r.message.count) {
                frappe.show_alert({
                    message: __('{0} shortlisted: {1}. Save to add them.', [r.message.count, frappe.utils.escape_html(r.message.applicants.join(', '))]),
                    indicator: 'green'
                }, 8);
            } else {
                frappe.show_alert({
                    message: __('No eligible shortlisted applicants for {0}.', [frappe.utils.escape_html(row.function)]),
                    indicator: 'orange'
                }, 8);
            }
        }
    });
}

frappe.ui.form.on('CXO Hiring Approval Function', {
    function: function(frm, cdt, cdn) {
        cxo_load_shortlisted_count(frm, cdt, cdn);
    }
});
