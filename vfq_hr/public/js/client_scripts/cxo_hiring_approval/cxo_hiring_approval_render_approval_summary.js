// Client Script: CXO Hiring Approval - Render Approval Summary (CXO Hiring Approval, Form)
var CXO_EXEC_ROLES = ['Head of OD & Total Rewards', 'CHRO', 'CAO', 'CEO / Final Approver'];

function cxo_is_exec_role() {
    return CXO_EXEC_ROLES.some(function(role) { return frappe.user_roles.includes(role); });
}

function cxo_is_sys_manager() {
    return frappe.user_roles.includes('System Manager');
}

function cxo_escape(v) {
    if (v === null || v === undefined || v === '') return '';
    return frappe.utils.escape_html(String(v));
}

function cxo_money(v) {
    if (!v) return '0';
    return format_number(v, null, 0);
}

function cxo_tile(label, value, color) {
    return '<div class="cxo-tile" style="--c:' + color + '">' +
        '<div class="cxo-tile-label">' + cxo_escape(label) + '</div>' +
        '<div class="cxo-tile-value">' + value + '</div>' +
    '</div>';
}

function cxo_table_block(title, headers, rows) {
    var html = '<div class="cxo-table-block">';
    html += '<div class="cxo-table-block-title">' + cxo_escape(title) + '</div>';
    if (!rows.length) {
        html += '<div style="padding:14px 2px;text-align:center;color:#8fa0cc;font-size:12px;">No ' + cxo_escape(title).toLowerCase() + ' added.</div>';
    } else {
        html += '<table><tr>';
        headers.forEach(function(h) { html += '<th>' + cxo_escape(h) + '</th>'; });
        html += '</tr>';
        rows.forEach(function(row) {
            html += '<tr>';
            row.forEach(function(cell, i) {
                if (i === 0) {
                    html += '<td class="cxo-row-main">' + (cell || '&mdash;') + '</td>';
                } else {
                    html += '<td>' + (cell || '&mdash;') + '</td>';
                }
            });
            html += '</tr>';
        });
        html += '</table>';
    }
    html += '</div>';
    return html;
}

function render_cxo_approval_summary(frm) {
    var field = frm.fields_dict['custom_approval_summary_html'];
    if (!field || !field.$wrapper) return;
    if (frm.is_new()) {
        field.$wrapper.empty();
        return;
    }

    var tiles = [
        cxo_tile('Total Applicants', cxo_escape(frm.doc.total_applicants || 0), '#64748b'),
        cxo_tile('Total Agreed Salary (USD / month)', '$ ' + cxo_money(frm.doc.custom_total_agreed_salary_monthly || ((frm.doc.total_agreed_salary_usd || 0) / 12)), '#2563eb'),
        cxo_tile('Company', cxo_escape(frm.doc.company) || '&mdash;', '#475569')
    ].join('');

    var functions_rows = (frm.doc.functions || []).map(function(row) {
        return [cxo_escape(row.function), cxo_escape(row.shortlisted_count || 0)];
    });

    var standard_rows = (frm.doc.standard_approvals || []).map(function(row) {
        return [cxo_escape(row.role), cxo_escape(row.vendor), cxo_escape(row.custom_project_name || row.project), cxo_escape(row.custom_cost_line_name || row.cost_line), cxo_escape(format_currency(row.approx_monthly_cost_impact || 0, 'USD')), cxo_escape(row.recommended_salary_range), cxo_escape(row.shortlisted_count || 0), cxo_escape(row.hr_comments)];
    });

    var exceptional_rows = (frm.doc.exceptional_approvals || []).map(function(row) {
        return [cxo_escape(row.role), cxo_escape(row.vendor), cxo_escape(row.custom_project_name || row.project), cxo_escape(row.custom_cost_line_name || row.cost_line), cxo_escape(format_currency(row.monthly_cost_impact || 0, 'USD')), cxo_escape(row.shortlisted_count || 0), cxo_escape(row.hr_comments)];
    });

    var html = '';
    html += '<div class="cxo-summary-card">';
    html += '<div class="cxo-summary-title">CXO Hiring Approval Summary</div>';
    html += '<div class="cxo-tiles">' + tiles + '</div>';
    html += '</div>';
    html += cxo_table_block('Functions', ['Function', 'Shortlisted Count'], functions_rows);
    html += cxo_table_block('Standard Approvals', ['Role', 'Vendor Name', 'Project', 'Cost Line', 'Monthly Cost Impact', 'Recommended Salary Range', 'Shortlisted Headcount', 'HR Comments'], standard_rows);
    html += cxo_table_block('Exceptional Approvals', ['Role', 'Vendor Name', 'Project', 'Cost Line', 'Monthly Cost Impact', 'Shortlisted Headcount', 'HR Comments'], exceptional_rows);

    html += '<style>' +
        '.cxo-summary-card{background:#eef1f8;border-radius:10px;padding:18px;margin-bottom:20px;}' +
        '.cxo-summary-title{font-size:13px;font-weight:700;color:#1f2d50;margin-bottom:12px;}' +
        '.cxo-tiles{display:flex;flex-wrap:wrap;gap:10px;}' +
        '.cxo-tile{flex:1 1 190px;min-width:160px;background:#fff;border-left:3px solid var(--c);border-radius:6px;padding:10px 14px;box-shadow:0 1px 2px rgba(16,24,40,.06);}' +
        '.cxo-tile-label{font-size:11.5px;font-weight:700;letter-spacing:.2px;text-transform:uppercase;color:#475569;margin-bottom:4px;}' +
        '.cxo-tile-value{font-size:15px;font-weight:600;color:#1f2d50;}' +
        '.cxo-table-block{background:#0f172a;border-radius:8px;padding:14px 16px 16px;margin-bottom:14px;}' +
        '.cxo-table-block-title{font-size:12.5px;font-weight:700;letter-spacing:.3px;text-transform:uppercase;color:#aab6d6;margin-bottom:10px;}' +
        '.cxo-table-block table{width:100%;border-collapse:collapse;font-size:12.5px;}' +
        '.cxo-table-block th{text-align:left;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:#8fa0cc;padding:6px 10px;border-bottom:1px solid rgba(255,255,255,.08);}' +
        '.cxo-table-block td{padding:9px 10px;color:#e6eaf5;border-bottom:1px solid rgba(255,255,255,.06);}' +
        '.cxo-table-block tr:last-child td{border-bottom:none;}' +
        '.cxo-row-main{font-weight:600;}' +
    '</style>';

    field.$wrapper.html(html);
}

function cxo_toggle_views(frm) {
    var is_exec = cxo_is_exec_role();
    var is_sys_mgr = cxo_is_sys_manager();
    var show_summary = (is_exec || is_sys_mgr) && !frm.is_new();
    var show_native = !is_exec || is_sys_mgr;

    frm.toggle_display('custom_approval_summary_section', show_summary);
    frm.toggle_display('custom_approval_summary_html', show_summary);

    frm.toggle_display('section_break_functions', show_native);
    frm.toggle_display('section_break_applicants', show_native);
    frm.toggle_display('functions', show_native);
    frm.toggle_display('standard_sb', show_native);
    frm.toggle_display('standard_approvals', show_native);
    frm.toggle_display('exceptional_sb', show_native);
    frm.toggle_display('exceptional_approvals', show_native);

    if (show_summary) {
        render_cxo_approval_summary(frm);
    } else if (frm.fields_dict['custom_approval_summary_html'] && frm.fields_dict['custom_approval_summary_html'].$wrapper) {
        frm.fields_dict['custom_approval_summary_html'].$wrapper.empty();
    }
}

frappe.ui.form.on('CXO Hiring Approval', {
    refresh: function(frm) {
        cxo_toggle_views(frm);
    }
});
