// Client Script: WP - Auto Calc Approved Roles (Workforce Plan, Form)
frappe.ui.form.on('Workforce Plan', {
    positions_add: function(frm) { calc_approved_roles(frm); },
    positions_remove: function(frm) { calc_approved_roles(frm); }
});

frappe.ui.form.on('Workforce Plan Position', {
    role_count: function(frm) { calc_approved_roles(frm); }
});

function calc_approved_roles(frm) {
    var total = 0;
    (frm.doc.positions || []).forEach(function(row) {
        total += (row.role_count || 0);
    });
    frm.set_value('approved_headcount', total);
}
