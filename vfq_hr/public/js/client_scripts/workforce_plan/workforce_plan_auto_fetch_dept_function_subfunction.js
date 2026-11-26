// Client Script: Workforce Plan - Auto-fetch Dept-Function-SubFunction (Workforce Plan, Form)
var WP_HR_ROLES = ['HR Manager', 'HR User', 'CHRO', 'System Manager'];
var WP_SENIOR_ROLES = ['Functional Head', 'Head of OD & Total Rewards', 'CAO', 'CEO / Final Approver', 'HR Manager', 'System Manager'];

function wp_is_hr_user() {
    return WP_HR_ROLES.some(function(role) { return frappe.user_roles.includes(role); });
}

function wp_is_senior_role() {
    return WP_SENIOR_ROLES.some(function(role) { return frappe.user_roles.includes(role); });
}

function wp_cache_own_employee_department(frm) {
    if (frm.__own_employee_dept !== undefined) {
        return Promise.resolve(frm.__own_employee_dept);
    }
    return frappe.db.get_value('Employee', {user_id: frappe.session.user}, 'department').then(function(r) {
        frm.__own_employee_dept = (r && r.message && r.message.department) ? r.message.department : null;
        return frm.__own_employee_dept;
    });
}

function wp_sync_header_department_from_positions(frm) {
    var dept = (frm.doc.positions && frm.doc.positions.length && frm.doc.positions[0].sub_function) || '';
    if (frm.doc.department !== dept) {
        frm.set_value('department', dept);
    }
}

function wp_cache_own_employee(frm) {
    if (frm.__own_employee_id !== undefined) {
        return Promise.resolve(frm.__own_employee_id);
    }
    return frappe.db.get_value('Employee', {user_id: frappe.session.user}, 'name').then(function(r) {
        frm.__own_employee_id = (r && r.message && r.message.name) ? r.message.name : null;
        return frm.__own_employee_id;
    });
}

frappe.ui.form.on('Workforce Plan', {
    onload: function(frm) {
        if (frm.is_new() && !frm.doc.department) {
            frappe.db.get_value('Employee', {user_id: frappe.session.user}, ['name', 'department', 'custom_function', 'custom_sub_function'])
                .then(r => {
                    if (r && r.message) {
                                                if (r.message.custom_function) frm.set_value('custom_function', r.message.custom_function);
                        if (r.message.custom_sub_function) frm.set_value('custom_sub_function', r.message.custom_sub_function);
                        frm.__own_employee_id = r.message.name || null;
                    }
                    set_dept_function_editability(frm);
                });
        } else {
            wp_cache_own_employee(frm);
            set_dept_function_editability(frm);
        }
        set_budget_line_query(frm);
    },
    refresh: function(frm) {
        set_dept_function_editability(frm);
        set_hiring_manager_editability(frm);
        set_budget_line_query(frm);
        wp_sync_header_department_from_positions(frm);
        render_approval_summary(frm);
        move_connections_to_tab(frm);
        if (frm.layout && frm.layout.refresh_tabs) { frm.layout.refresh_tabs(); }
    },
    cost_center: function(frm) { set_budget_line_query(frm); },
    fiscal_year: function(frm) { set_budget_line_query(frm); },
    approved_budget: function(frm) { render_approval_summary(frm); },
    committed_budget: function(frm) { render_approval_summary(frm); },
    consumed_budget: function(frm) { render_approval_summary(frm); },
    remaining_budget: function(frm) { render_approval_summary(frm); },
    total_budget_impact: function(frm) { render_approval_summary(frm); },
    budget_line: function(frm) { render_approval_summary(frm); },
    validate: function(frm) {
        var promises = [];
        var missing_dept = (frm.doc.positions || []).filter(function(row) { return !row.sub_function; });
        if (missing_dept.length) {
            promises.push(wp_cache_own_employee_department(frm).then(function(dept) {
                if (dept) {
                    missing_dept.forEach(function(row) {
                        frappe.model.set_value(row.doctype, row.name, 'sub_function', dept);
                    });
                }
                wp_sync_header_department_from_positions(frm);
            }));
        }
        if (!wp_is_hr_user()) {
            var missing_hm = (frm.doc.positions || []).filter(function(row) { return !row.hiring_manager; });
            if (missing_hm.length) {
                promises.push(wp_cache_own_employee(frm).then(function(emp_id) {
                    if (emp_id) {
                        missing_hm.forEach(function(row) {
                            frappe.model.set_value(row.doctype, row.name, 'hiring_manager', emp_id);
                        });
                    }
                }));
            }
        }
        if (!promises.length) return;
        return Promise.all(promises);
    }
});

frappe.ui.form.on('Workforce Plan Position', {
    positions_add: function(frm, cdt, cdn) {
        wp_cache_own_employee_department(frm).then(function(dept) {
            if (dept) {
                frappe.model.set_value(cdt, cdn, 'sub_function', dept);
            }
            wp_sync_header_department_from_positions(frm);
        });
        if (wp_is_hr_user()) return;
        wp_cache_own_employee(frm).then(function(emp_id) {
            if (emp_id) {
                frappe.model.set_value(cdt, cdn, 'hiring_manager', emp_id);
            }
        });
    },
    positions_remove: function(frm) { wp_sync_header_department_from_positions(frm); render_approval_summary(frm); },
    sub_function: function(frm) { wp_sync_header_department_from_positions(frm); render_approval_summary(frm); },
    position: function(frm) { render_approval_summary(frm); },
    role_count: function(frm) { render_approval_summary(frm); },
    role_type: function(frm) { render_approval_summary(frm); },
    existing_cost_usd: function(frm) { render_approval_summary(frm); },
    critical_info: function(frm) { render_approval_summary(frm); },
    scope: function(frm) { render_approval_summary(frm); },
    role_description: function(frm) { render_approval_summary(frm); },
    experience_required: function(frm) { render_approval_summary(frm); }
});

function set_dept_function_editability(frm) {
    var is_hr = wp_is_hr_user();
    
    frm.set_df_property('custom_function', 'read_only', is_hr ? 0 : 1);
    frm.set_df_property('custom_sub_function', 'read_only', is_hr ? 0 : 1);
    
    frm.refresh_field('custom_function');
    frm.refresh_field('custom_sub_function');
}

function set_hiring_manager_editability(frm) {
    var is_hr = wp_is_hr_user();
    var grid = frm.fields_dict['positions'].grid;
    grid.update_docfield_property('hiring_manager', 'read_only', is_hr ? 0 : 1);
    grid.refresh();
}

function set_budget_line_query(frm) {
    frm.set_query('budget_line', function() {
        if (!frm.doc.cost_center || !frm.doc.fiscal_year) {
            return {filters: {name: ['in', []]}};
        }
        return {
            filters: {
                cost_center: frm.doc.cost_center,
                fiscal_year: frm.doc.fiscal_year,
                docstatus: 1
            }
        };
    });
}

function wp_escape(val) {
    if (val === null || val === undefined) return '';
    return frappe.utils.escape_html(String(val));
}

function wp_money(val) {
    if (val === null || val === undefined || val === '') return '<span style="color:#9aa3b2;">&mdash;</span>';
    var num = flt(val);
    try {
        return format_currency(num, 'USD');
    } catch (e) {
        return '$' + num.toLocaleString();
    }
}

function wp_tile(label, value, color) {
    return '' +
        '<div style="flex:1 1 170px;min-width:150px;background:#ffffff;border-left:3px solid ' + color + ';' +
        'border-radius:6px;padding:9px 13px;box-shadow:0 1px 2px rgba(16,24,40,0.06);">' +
        '<div style="font-size:11.5px;font-weight:700;letter-spacing:.2px;color:#475569;margin-bottom:4px;white-space:normal;word-break:break-word;line-height:1.3;">' + wp_escape(label) + '</div>' +
        '<div style="font-size:12.5px;font-weight:500;color:#1f2d50;white-space:normal;word-break:break-word;overflow-wrap:break-word;line-height:1.4;">' + value + '</div>' +
        '</div>';
}

function wp_role_pill(role_type) {
    var is_existing = (role_type === 'Existing Role');
    return '<span style="font-size:10.5px;font-weight:700;padding:3px 9px;border-radius:999px;white-space:nowrap;flex-shrink:0;' +
        (is_existing ? 'background:#16a34a;color:#fff;' : 'background:#3b5fc4;color:#fff;') + '">' +
        (wp_escape(role_type) || 'New Role') + '</span>';
}

function wp_detail_item(label, value, full) {
    return '<div style="' + (full ? 'grid-column:1 / -1;' : '') + '">' +
        '<div style="font-size:10px;font-weight:700;letter-spacing:.3px;text-transform:uppercase;color:#2563eb;margin-bottom:3px;">' + wp_escape(label) + '</div>' +
        '<div style="font-size:12px;line-height:1.5;color:#334155;white-space:normal;word-break:break-word;overflow-wrap:break-word;">' +
        (value || '<span style="color:#9aa3b2;">&mdash;</span>') + '</div>' +
        '</div>';
}

function wp_resolve_budget_title(frm) {
    var id = frm.doc.budget_line;
    if (!id) return '';
    if (!frm.__budget_titles) frm.__budget_titles = {};
    if (frm.__budget_titles[id] !== undefined) return frm.__budget_titles[id];
    frm.__budget_titles[id] = id;
    frappe.db.get_value('Budget', id, 'custom_budget_title').then(function(r) {
        var title = (r && r.message && r.message.custom_budget_title) ? r.message.custom_budget_title : id;
        if (title && title !== id) {
            frm.__budget_titles[id] = title;
            render_approval_summary(frm);
        }
    });
    return id;
}

function render_approval_summary(frm) {
    var field = frm.fields_dict['custom_approval_summary_html'];
    if (!field || !field.$wrapper) return;
    if (!wp_is_senior_role()) {
        field.$wrapper.empty();
        return;
    }

    if (!frm.__wp_appsum_open) frm.__wp_appsum_open = {};

    var budget_label = wp_resolve_budget_title(frm);

    var tiles = [
        wp_tile('Cost Center', wp_escape(frm.doc.cost_center) || '&mdash;', '#64748b'),
        wp_tile('Budget Line', wp_escape(budget_label) || '&mdash;', '#475569'),
        wp_tile('Approved Budget', wp_money(frm.doc.approved_budget), '#2563eb'),
        wp_tile('Total Budget Impact', wp_money(frm.doc.total_budget_impact), '#7c3aed')
    ].join('');

    var positions = frm.doc.positions || [];

    var rows_html;
    if (!positions.length) {
        rows_html = '<div style="padding:16px;text-align:center;color:#9aa3b2;font-size:12px;">No positions added to this plan yet.</div>';
    } else {
        rows_html = positions.map(function(row, i) {
            var is_open = !!frm.__wp_appsum_open[row.name];
            var cost_html = (row.role_type === 'Existing Role') ? wp_money(row.existing_cost_usd) : '<span style="color:#aab6d6;">&mdash;</span>';

            var main_row = '' +
                '<div class="wp-main-row" style="display:flex;flex-wrap:wrap;align-items:center;gap:12px;row-gap:6px;padding:10px 14px;' +
                'background:#1f2d50;color:#ffffff;cursor:pointer;user-select:none;">' +
                '<div style="width:22px;height:22px;border-radius:5px;background:rgba(255,255,255,0.15);font-size:11px;font-weight:700;' +
                'display:flex;align-items:center;justify-content:center;flex-shrink:0;">' + (i + 1) + '</div>' +
                '<div style="flex:1 1 220px;min-width:150px;">' +
                '<div style="font-size:13px;font-weight:700;line-height:1.3;">' + (wp_escape(row.position) || '&mdash;') + '</div>' +
                '<div style="font-size:11px;color:#aab6d6;margin-top:1px;">' + (wp_escape(row.sub_function) || '&mdash;') + '</div>' +
                '</div>' +
                wp_role_pill(row.role_type) +
                '<div style="flex:0 1 70px;min-width:50px;">' +
                '<div style="font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:#8fa0cc;margin-bottom:1px;">Count</div>' +
                '<div style="font-size:12px;font-weight:600;color:#fff;">' + (wp_escape(row.role_count) || '&mdash;') + '</div>' +
                '</div>' +
                '<div style="flex:1 1 150px;min-width:110px;">' +
                '<div style="font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:#8fa0cc;margin-bottom:1px;">Experience</div>' +
                '<div style="font-size:12px;font-weight:600;color:#fff;white-space:normal;word-break:break-word;">' + (wp_escape(row.experience_required) || '&mdash;') + '</div>' +
                '</div>' +
                '<div style="font-size:12.5px;font-weight:700;color:#fff;text-align:right;flex-shrink:0;min-width:70px;">' + cost_html + '</div>' +
                '<div class="wp-chevron" style="flex-shrink:0;font-size:12px;color:#aab6d6;transition:transform .15s ease;' +
                'transform:rotate(' + (is_open ? '90deg' : '0deg') + ');">&#9656;</div>' +
                '</div>';

            var detail_strip = '' +
                '<div class="wp-detail-strip" style="display:' + (is_open ? 'block' : 'none') + ';padding:13px 16px 14px;background:#fbfcfe;border-top:1px solid #eef1f7;">' +
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px 22px;">' +
                wp_detail_item('Critical Info', wp_escape(row.critical_info)) +
                wp_detail_item('Scope', wp_escape(row.scope)) +
                wp_detail_item('Role Description', wp_escape(row.role_description), true) +
                '</div>' +
                '</div>';

            return '<div class="wp-rowblock" data-row-name="' + wp_escape(row.name) + '" style="background:#fff;border:1px solid #e5e9f1;' +
                'border-radius:8px;box-shadow:0 1px 2px rgba(16,24,40,0.06);margin-bottom:10px;overflow:hidden;">' +
                main_row + detail_strip + '</div>';
        }).join('');
    }

    var positions_block = '' +
        '<div style="margin-top:4px;">' +
        '<div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:10px;">' +
        '<div style="font-size:13px;font-weight:700;color:#1f2d50;">Positions (' + positions.length + ')</div>' +
        '<div style="font-size:11.5px;color:#64748b;font-weight:500;">Click a row to expand full details</div>' +
        '</div>' +
        rows_html +
        '</div>';

    var html = '' +
        '<div style="background:#f8f9fc;border:1px solid #e3e7f0;border-radius:10px;padding:16px 18px 18px;margin-bottom:6px;">' +
        '<div style="font-size:14px;font-weight:700;color:#1f2d50;margin-bottom:12px;">Workforce Plan Summary</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px;">' + tiles + '</div>' +
        positions_block +
        '</div>';

    field.$wrapper.html(html);

    field.$wrapper.off('click.wpToggle').on('click.wpToggle', '.wp-main-row', function() {
        var $block = $(this).closest('.wp-rowblock');
        var row_name = $block.attr('data-row-name');
        var now_open = !($block.find('.wp-detail-strip').is(':visible'));
        frm.__wp_appsum_open[row_name] = now_open;
        $block.find('.wp-detail-strip').toggle(now_open);
        $block.find('.wp-chevron').css('transform', 'rotate(' + (now_open ? '90deg' : '0deg') + ')');
    });
}

// ---- Relocate the built-in Connections dashboard into its own tab ----

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
