// Client Script: CXO Hiring Approval - CAO CEO Field Visibility (CXO Hiring Approval, Form)
frappe.ui.form.on("CXO Hiring Approval", {
    refresh(frm) {
        apply_cxo_approval_visibility(frm);
    },
    workflow_state(frm) {
        apply_cxo_approval_visibility(frm);
    }
});

function apply_cxo_approval_visibility(frm) {
    const roles = frappe.user_roles || [];
    const is_cao = roles.includes("CAO");
    const is_ceo = roles.includes("CEO / Final Approver");
    const is_sys_manager = roles.includes("System Manager");

    const cao_done = !!frm.doc.cao_approved_by || !!frm.doc.cao_remarks ||
        ["Pending CEO Approval", "Approved", "Approved to onboard"].includes(frm.doc.workflow_state);
    const ceo_done = !!frm.doc.ceo_approved_by || !!frm.doc.ceo_remarks ||
        ["Approved", "Approved to onboard"].includes(frm.doc.workflow_state);

    const show_cao_section = is_cao || is_sys_manager || cao_done;
    const show_ceo_section = is_ceo || is_sys_manager || ceo_done;

    ["section_break_cao", "cao_remarks", "column_break_cao", "cao_approved_by", "cao_approved_on"]
        .forEach(f => frm.toggle_display(f, show_cao_section));
    ["section_break_ceo", "ceo_remarks", "column_break_ceo", "ceo_approved_by", "ceo_approved_on"]
        .forEach(f => frm.toggle_display(f, show_ceo_section));
}
