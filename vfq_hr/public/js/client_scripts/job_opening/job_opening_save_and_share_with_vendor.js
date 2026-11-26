// Client Script: Job Opening - Save and Share with Vendor (Job Opening, Form)
frappe.ui.form.on('Job Opening', {
    refresh: function(frm) {
        if (frm.doc.status === 'Open & To be shared with vendor') {
            frm.disable_form();
            frm.disable_save();
            frm.set_intro(__('This opening has been shared with the vendor. It is locked and cannot be changed.'), 'blue');
            return;
        }
        var confidential = frm.doc.custom_confidential_hiring;
        var needs_date = !frm.is_new() && !confidential && frm.doc.status !== 'Closed';
        frm.set_df_property('custom_vendor_push_date', 'reqd', needs_date ? 1 : 0);
        if (!frm.is_new() && !confidential && frm.doc.status === 'Open') {
            frm.add_custom_button(__('Save & Share with vendor'), function() {
                var d = new frappe.ui.Dialog({
                    title: __('Share role with vendor'),
                    fields: [{ fieldname: 'share_date', fieldtype: 'Datetime', label: __('Role sharing date'), reqd: 1, default: frappe.datetime.now_datetime() }],
                    primary_action_label: __('Save & Share'),
                    primary_action: function(values) {
                        d.hide();
                        frm.set_value('custom_vendor_push_date', values.share_date);
                        frm.save();
                    }
                });
                d.show();
            }).addClass('btn-primary');
        }
    }
});
