// Client Script: Employee Exit - Field Ownership View (Employee Exit, Form)
// Field ownership (read-only view). The server-side "Field Ownership Guard" is what enforces it;
// this only greys out the parts that belong to someone else so nobody types into them.
(function () {
  var CFG = {"emp_states":["Draft"],"emp":["exit_type","custom_exit_reason","exit_reason","notice_date","custom_signed_resignation","knowledge_transfer_notes"],"mgr":["custom_exit_reason","knowledge_transfer_notes"],"hr":["employee","rehire_eligible","custom_signed_acceptance","hr_approver","exit_interview_notes"],"tables":{"activities":{"emp":[],"mgr":[],"hr":["status","remarks"],"self_only":1}}};
  function applyOwnership(frm) {
    if (frm.is_new() || !frm.doc.employee) return;
    frappe.call({ method: "get_review_access", args: { employee: frm.doc.employee } }).then(function (r) {
      var a = (r && r.message) || {};
      var state = frm.doc.workflow_state || "Draft";
      var empOk = a.is_self && CFG.emp_states.indexOf(state) !== -1;
      function allowed(list) {
        var s = {};
        if (empOk) list.emp.forEach(function (f) { s[f] = 1; });
        if (a.is_mgr || a.is_hr) list.mgr.forEach(function (f) { s[f] = 1; });
        if (a.is_hr) list.hr.forEach(function (f) { s[f] = 1; });
        return s;
      }
      var can = allowed(CFG);
      CFG.emp.concat(CFG.mgr, CFG.hr).forEach(function (f) {
        if (!frm.fields_dict[f]) return;
        var orig = (frappe.meta.get_docfield(frm.doctype, f) || {}).read_only || 0;
        frm.set_df_property(f, "read_only", (a.is_sys || can[f]) ? orig : 1);
      });
      Object.keys(CFG.tables).forEach(function (tf) {
        var t = CFG.tables[tf];
        var fd = frm.fields_dict[tf];
        if (!fd || !fd.grid) return;
        var restrict = !a.is_sys && (!t.self_only || a.is_self);
        var tcan = allowed(t);
        var cdt = fd.grid.doctype;
        t.emp.concat(t.mgr, t.hr).forEach(function (f) {
          var orig = (frappe.meta.get_docfield(cdt, f) || {}).read_only || 0;
          fd.grid.update_docfield_property(f, "read_only", (!restrict || tcan[f]) ? orig : 1);
        });
        var lockRows = restrict && !a.is_hr;
        frm.set_df_property(tf, "cannot_add_rows", lockRows ? 1 : 0);
        frm.set_df_property(tf, "cannot_delete_rows", lockRows ? 1 : 0);
        fd.grid.refresh();
      });
    });
  }
  frappe.ui.form.on("Employee Exit", {
    refresh: function (frm) { applyOwnership(frm); },
    after_workflow_action: function (frm) { applyOwnership(frm); }
  });
})();
