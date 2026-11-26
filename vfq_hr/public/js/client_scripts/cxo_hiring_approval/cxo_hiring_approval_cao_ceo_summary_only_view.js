// Client Script: CXO Hiring Approval - CAO CEO Summary Only View (CXO Hiring Approval, Form)
// CAO and CEO review the Approval Summary and enter their remarks only.
const CXO_SUMMARY_ONLY_HIDDEN_FIELDS = [
    'title', 'company', 'section_break_applicants', 'functions', 'applicants',
    'section_break_totals', 'total_applicants', 'column_break_totals_1', 'exchange_rate_used', 'exchange_rate_date',
    'section_break_totals_2', 'total_agreed_salary_usd', 'column_break_totals_2', 'total_agreed_salary_qar',
    'column_break_cao', 'cao_approved_by', 'cao_approved_on',
    'column_break_ceo', 'ceo_approved_by', 'ceo_approved_on',
    'custom_hod_cb', 'custom_hod_approved_by', 'custom_hod_approved_on',
    'custom_chro_cb', 'custom_chro_approved_by', 'custom_chro_approved_on',
    'amended_from', 'standard_sb', 'standard_approvals', 'exceptional_sb', 'exceptional_approvals'
];

function cxo_is_summary_only_user() {
    const roles = frappe.user_roles || [];
    return (roles.includes('CAO') || roles.includes('CEO / Final Approver') || roles.includes('CHRO') || roles.includes('Head of OD & Total Rewards')) && !roles.includes('System Manager');
}

function cxo_apply_remarks_lock(frm) {
    const roles = frappe.user_roles || [];
    const state = frm.doc.workflow_state;
    const cao_can_edit = state === 'Pending CAO Approval' && roles.includes('CAO');
    const ceo_can_edit = state === 'Pending CEO Approval' && roles.includes('CEO / Final Approver');
    frm.set_df_property('cao_remarks', 'read_only', cao_can_edit ? 0 : 1);
    frm.set_df_property('ceo_remarks', 'read_only', ceo_can_edit ? 0 : 1);
    const hod_can_edit = state === 'Pending Head of OD Approval' && roles.includes('Head of OD & Total Rewards');
    const chro_can_edit = state === 'Pending CHRO Approval' && roles.includes('CHRO');
    if (frm.fields_dict.custom_hod_remarks) frm.set_df_property('custom_hod_remarks', 'read_only', hod_can_edit ? 0 : 1);
    if (frm.fields_dict.custom_chro_remarks) frm.set_df_property('custom_chro_remarks', 'read_only', chro_can_edit ? 0 : 1);
}

function cxo_apply_summary_only_view(frm) {
    cxo_apply_remarks_lock(frm);
    if (frm.is_new() || !cxo_is_summary_only_user()) return;
    CXO_SUMMARY_ONLY_HIDDEN_FIELDS.forEach(function(fieldname) {
        if (frm.fields_dict[fieldname]) {
            frm.set_df_property(fieldname, 'hidden', 1);
        }
    });
}

frappe.ui.form.on('CXO Hiring Approval', {
    refresh: function(frm) {
        [0, 300, 900, 2000].forEach(function(delay) {
            setTimeout(function() { cxo_apply_summary_only_view(frm); }, delay);
        });
    },
    workflow_state: function(frm) {
        cxo_apply_summary_only_view(frm);
    }
});
