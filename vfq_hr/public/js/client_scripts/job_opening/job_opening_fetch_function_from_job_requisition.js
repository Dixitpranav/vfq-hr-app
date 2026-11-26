// Client Script: Job Opening - Fetch Function from Job Requisition (Job Opening, Form)
frappe.ui.form.on('Job Opening', {
  job_requisition: function(frm) { fetch_function_from_jr(frm); },
  designation: function(frm) { fetch_function_from_jr(frm); }
});
function fetch_function_from_jr(frm) {
  if (!frm.doc.job_requisition || !frm.doc.designation) { return; }
  frappe.call({
    method: 'frappe.client.get',
    args: { doctype: 'Job Requisition', name: frm.doc.job_requisition }
  }).then(function(r) {
    var jr = r.message;
    if (!jr || !jr.custom_roles) { return; }
    var match = jr.custom_roles.find(function(row) { return row.designation === frm.doc.designation; });
    if (match) {
      frm.set_value('custom_function', match.custom_function);
      frm.set_value('custom_sub_function', match.custom_sub_function);
    }
  });
}
