// Client Script: Job Applicant - Allow Shared Openings (Job Applicant, Form)
frappe.ui.form.on('Job Applicant', {
    refresh: function(frm) {
        frm.set_query('job_title', function() {
            return { filters: { status: ['in', ['Open', 'Open & To be shared with vendor']] } };
        });
    }
});
