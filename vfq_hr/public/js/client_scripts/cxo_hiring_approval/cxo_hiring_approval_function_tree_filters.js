// Client Script: CXO Hiring Approval - Function Tree Filters (CXO Hiring Approval, Form)
frappe.ui.form.on('CXO Hiring Approval', {
  refresh: function(frm) {
    const topLevelOnly = function() { return { filters: [['parent_function','is','not set']] }; };
    frm.set_query('function', 'functions', topLevelOnly);
    frm.set_query('function', 'applicants', topLevelOnly);
    frm.set_query('function', 'standard_approvals', topLevelOnly);
    frm.set_query('function', 'exceptional_approvals', topLevelOnly);
  }
});
