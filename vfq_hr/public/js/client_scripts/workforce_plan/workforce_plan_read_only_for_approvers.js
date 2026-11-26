// Client Script: Workforce Plan - Read Only for Approvers (Workforce Plan, Form)
// Workforce Plan editing rules:
// Draft: only the creator can edit. In approval: nobody can edit.
// In approval the creator can ask the current approver to send the plan back for review.
function wp_in_approval(frm) {
    return frm.doc.docstatus === 0 && /^Pending /.test(frm.doc.workflow_state || '');
}

function wp_lock_form(frm) {
    if (frm.is_new() || frm.doc.docstatus !== 0 || frappe.session.user === 'Administrator') return;
    if (frappe.session.user === frm.doc.owner && !wp_in_approval(frm)) return;
    var skip = ['Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button', 'Heading', 'Fold'];
    (frm.meta.fields || []).forEach(function(df) {
        if (skip.indexOf(df.fieldtype) === -1) {
            frm.set_df_property(df.fieldname, 'read_only', 1);
        }
    });
    var grid = frm.fields_dict.positions && frm.fields_dict.positions.grid;
    if (grid) {
        grid.cannot_add_rows = true;
        grid.df.cannot_delete_rows = 1;
        grid.refresh();
    }
    frm.disable_save();
}

function wp_open_send_back_dialog(frm) {
    var dialog = new frappe.ui.Dialog({
        title: __('Request Send Back for Review'),
        fields: [{
            fieldname: 'reason',
            fieldtype: 'Small Text',
            label: __('What needs to be changed?'),
            reqd: 1
        }],
        primary_action_label: __('Send Request to Approver'),
        primary_action: function(values) {
            var reason = (values.reason || '').trim();
            if (reason.length < 10) {
                frappe.msgprint(__('Enter a clear reason of at least 10 characters.'));
                return;
            }
            dialog.disable_primary_action();
            frappe.call({
                method: 'request_workforce_plan_send_back',
                args: { plan: frm.doc.name, reason: reason },
                freeze: true,
                callback: function(r) {
                    if (r.exc) return;
                    dialog.hide();
                    frappe.show_alert({ message: __('Request sent to the approver'), indicator: 'green' });
                    frm.reload_doc();
                },
                always: function() {
                    dialog.enable_primary_action();
                }
            });
        }
    });
    dialog.show();
}

function wp_send_back_actions(frm) {
    if (frm.is_new() || !wp_in_approval(frm)) return;
    var label = __('Request Send Back for Review');
    var links = frm.page.wrapper.find('.actions-btn-group .dropdown-menu a');
    if (cint(frm.doc.custom_send_back_requested)) {
        links.filter(function() { return $(this).text().trim() === __('Approve'); }).closest('li').hide();
        return;
    }
    if (frappe.session.user !== frm.doc.owner) return;
    var exists = links.filter(function() { return $(this).text().trim() === label; }).length;
    if (!exists) {
        frm.page.add_action_item(label, function() { wp_open_send_back_dialog(frm); });
        frm.page.show_actions_menu();
    }
}

frappe.ui.form.on('Workforce Plan', {
    refresh: function(frm) {
        wp_lock_form(frm);
        if (wp_in_approval(frm) && cint(frm.doc.custom_send_back_requested)) {
            frm.set_intro(__('Send back requested by {0} on {1}. Reason: "{2}" Use Send Back for Review or Reject; Approve is unavailable until this is resolved.', [
                frappe.utils.escape_html(frm.doc.custom_send_back_requested_by || ''),
                frappe.datetime.str_to_user(frm.doc.custom_send_back_requested_on || ''),
                frappe.utils.escape_html(frm.doc.custom_send_back_reason || '')
            ]), 'orange');
        }
        [300, 900, 2000].forEach(function(delay) {
            setTimeout(function() {
                wp_lock_form(frm);
                wp_send_back_actions(frm);
            }, delay);
        });
    }
});
