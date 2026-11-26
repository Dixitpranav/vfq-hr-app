// Client Script: Workforce Plan - Function Tree Filters (Workforce Plan, Form)
frappe.ui.form.on('Workforce Plan', {
  refresh: function(frm) { set_position_function_filters(frm); init_function_restrictions(frm); },
  department: function(frm) {
    set_position_function_filters(frm);
    var changed = false;
    (frm.doc.positions || []).forEach(function(row) {
      if (row.sub_function) { frappe.model.set_value(row.doctype, row.name, 'sub_function', null); changed = true; }
    });
    if (changed) {
      frm.refresh_field('positions');
      frappe.show_alert({message: 'Plan Department changed — cleared the Department on existing position rows. Please re-pick a department within the new plan Department for each row.', indicator: 'orange'});
    }
  }
});

frappe.ui.form.on('Workforce Plan Position', {
  function: function(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.custom_sub_function) { frappe.model.set_value(cdt, cdn, 'custom_sub_function', null); }
  },
  positions_add: function(frm, cdt, cdn) {
    set_position_function_filters(frm);
    if (!frm.__is_hr_user && frm.__own_function) {
      frappe.model.set_value(cdt, cdn, 'function', frm.__own_function);
    }
  }
});

function set_position_function_filters(frm) {
  frm.set_query('function', 'positions', function() {
    return { filters: [['is_group', '=', 1]] };
  });
  frm.set_query('custom_sub_function', 'positions', function(doc, cdt, cdn) {
    const row = locals[cdt][cdn];
    return {
      filters: row.function
        ? [['is_group', '=', 0], ['parent_function', '=', row.function]]
        : [['is_group', '=', 0], ['name', 'in', []]]
    };
  });
  frm.set_query('sub_function', 'positions', function() {
    if (!frm.doc.department) {
      return {};
    }
    return { filters: [['name', 'descendants of (inclusive)', frm.doc.department]] };
  });
}

function init_function_restrictions(frm) {
  frm.__is_hr_user = frappe.user.has_role(['HR Manager', 'HR User']);
  if (frm.fields_dict['positions'] && frm.fields_dict['positions'].grid) {
    frm.fields_dict['positions'].grid.update_docfield_property('function', 'read_only', frm.__is_hr_user ? 0 : 1);
    frm.fields_dict['positions'].grid.refresh();
  }
  if (frm.__is_hr_user) return;
  frappe.db.get_value('Employee', { user_id: frappe.session.user }, 'custom_function').then(function(r) {
    frm.__own_function = (r && r.message) ? r.message.custom_function : null;
    if (!frm.__own_function) return;
    var changed = false;
    (frm.doc.positions || []).forEach(function(row) {
      if (!row.function) { frappe.model.set_value(row.doctype, row.name, 'function', frm.__own_function); changed = true; }
    });
    if (changed) frm.refresh_field('positions');
  });
}

// Keep the row Department picker usable when the hidden plan Department is blank.
frappe.ui.form.on('Workforce Plan', {
    refresh: function(frm) {
        if (frm.doc.docstatus !== 0 || frm.doc.department) return;
        frappe.db.get_value('Employee', { user_id: frappe.session.user }, 'department').then(function(r) {
            var dept = r && r.message && r.message.department;
            if (dept && !frm.doc.department) {
                frm.doc.department = dept;
                frm.refresh_field('department');
            }
        });
    }
});

frappe.ui.form.on('Workforce Plan Position', {
    sub_function: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.sub_function && !frm.doc.department) {
            frm.doc.department = row.sub_function;
            frm.refresh_field('department');
        }
    }
});
