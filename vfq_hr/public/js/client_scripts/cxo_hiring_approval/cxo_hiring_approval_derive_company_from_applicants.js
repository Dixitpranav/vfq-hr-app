// Client Script: CXO Hiring Approval - Derive Company from Applicants (CXO Hiring Approval, Form)
async function derive_company(frm) {
    let rows = (frm.doc.applicants || []).filter(r => r.job_applicant);
    if (!rows.length) return;
    let companies = new Set();
    for (const r of rows) {
        const res = await frappe.db.get_value('Job Applicant', r.job_applicant, 'custom_company');
        if (res && res.message && res.message.custom_company) {
            companies.add(res.message.custom_company);
        }
    }
    if (companies.size > 1) {
        frappe.show_alert({message: 'Applicants belong to different companies (' + Array.from(companies).join(', ') + '). This will be blocked on save.', indicator: 'red'}, 7);
    } else if (companies.size === 1) {
        frm.set_value('company', Array.from(companies)[0]);
    }
}

frappe.ui.form.on('CXO Hiring Approval', {
    refresh: function(frm) {
        derive_company(frm);
    }
});

frappe.ui.form.on('CXO Hiring Approval Applicant', {
    job_applicant: function(frm, cdt, cdn) {
        derive_company(frm);
    },
    applicants_add: function(frm) {
        derive_company(frm);
    },
    applicants_remove: function(frm) {
        derive_company(frm);
    }
});
