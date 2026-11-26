// Client Script: CXO Hiring Approval - Send Back Reason Popup (CXO Hiring Approval, Form)
// Asks the CAO or CEO for a reason before a batch is sent back for review.
frappe.ui.form.on('CXO Hiring Approval', {
    before_workflow_action: function(frm) {
        if (frm.selected_workflow_action !== 'Send Back for Review') return;
        frappe.dom.unfreeze();
        return new Promise(function(resolve, reject) {
            var confirmed = false;
            var dialog = new frappe.ui.Dialog({
                title: __('Send Back for Review'),
                fields: [{
                    fieldname: 'reason',
                    fieldtype: 'Small Text',
                    label: __('Reason for sending back'),
                    description: __('This will be saved in the comments on this form.'),
                    reqd: 1
                }],
                primary_action_label: __('Send Back'),
                primary_action: function(values) {
                    var reason = (values.reason || '').trim();
                    if (reason.length < 10) {
                        frappe.msgprint(__('Enter a clear reason of at least 10 characters.'));
                        return;
                    }
                    dialog.disable_primary_action();
                    frappe.call({
                        method: 'save_cxo_send_back_reason',
                        args: { batch: frm.doc.name, reason: reason },
                        callback: function(r) {
                            if (r.exc) return;
                            confirmed = true;
                            dialog.hide();
                            frappe.dom.freeze();
                            resolve();
                        },
                        always: function() {
                            dialog.enable_primary_action();
                        }
                    });
                }
            });
            dialog.onhide = function() {
                if (!confirmed) {
                    frm.selected_workflow_action = null;
                    reject();
                }
            };
            dialog.show();
        });
    }
});
