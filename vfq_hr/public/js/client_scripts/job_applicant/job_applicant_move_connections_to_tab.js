// Client Script: Job Applicant - Move Connections to Tab (Job Applicant, Form)
frappe.ui.form.on('Job Applicant', {
    refresh: function(frm) {
        move_connections_to_tab(frm);
        if (frm.layout && frm.layout.refresh_tabs) { frm.layout.refresh_tabs(); }
    }
});

function move_connections_to_tab(frm) {
    if (!frm.dashboard || !frm.dashboard.parent || !frm.dashboard.parent.length) return;
    if (!frm.layout || !frm.layout.tabs) return;
    var conn_tab = frm.layout.tabs.filter(function(t) {
        return t.df && t.df.fieldname === 'custom_connections_tab';
    })[0];
    if (!conn_tab || !conn_tab.wrapper) return;
    if (frm.dashboard.parent.parent().is(conn_tab.wrapper)) return;
    frm.dashboard.parent.appendTo(conn_tab.wrapper);
}
