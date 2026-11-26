// Client Script: Job Applicant - Function Tree Filters (Job Applicant, Form)
frappe.ui.form.on('Job Applicant', {
  refresh: function(frm) { set_function_filters(frm); },
  custom_function: function(frm) {
    set_function_filters(frm);
    if (frm.doc.custom_sub_function) { frm.set_value('custom_sub_function', ''); }
  }
});
function set_function_filters(frm) {
  frm.set_query('custom_function', function() {
    return { filters: [['parent_function','is','not set']] };
  });
  frm.set_query('custom_sub_function', function() {
    return { filters: [['parent_function','=', frm.doc.custom_function || '']] };
  });
}
