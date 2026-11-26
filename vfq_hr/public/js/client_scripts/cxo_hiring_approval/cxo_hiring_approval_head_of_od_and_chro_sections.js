// Client Script: CXO Hiring Approval - Head of OD and CHRO Sections (CXO Hiring Approval, Form)
// Shows the Head of OD and CHRO approval sections to that approver, to System Managers,
// and to everyone once that stage has been passed (same rule as the CAO and CEO sections).
function cxo_new_stage_visibility(frm) {
    const roles = frappe.user_roles || [];
    const sys = roles.includes('System Manager');
    const st = frm.doc.workflow_state;
    const after_hod = ['Pending CHRO Approval', 'Pending CAO Approval', 'Pending CEO Approval', 'Approved', 'Approved to onboard'].includes(st);
    const after_chro = ['Pending CAO Approval', 'Pending CEO Approval', 'Approved', 'Approved to onboard'].includes(st);
    const show_hod = roles.includes('Head of OD & Total Rewards') || sys || !!frm.doc.custom_hod_approved_by || !!frm.doc.custom_hod_remarks || after_hod;
    const show_chro = roles.includes('CHRO') || sys || !!frm.doc.custom_chro_approved_by || !!frm.doc.custom_chro_remarks || after_chro;
    ['custom_hod_section', 'custom_hod_remarks', 'custom_hod_cb', 'custom_hod_approved_by', 'custom_hod_approved_on'].forEach(f => frm.toggle_display(f, show_hod));
    ['custom_chro_section', 'custom_chro_remarks', 'custom_chro_cb', 'custom_chro_approved_by', 'custom_chro_approved_on'].forEach(f => frm.toggle_display(f, show_chro));
}
frappe.ui.form.on('CXO Hiring Approval', {
    refresh: cxo_new_stage_visibility,
    workflow_state: cxo_new_stage_visibility
});
