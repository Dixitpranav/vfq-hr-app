// Client Script: Job Applicant - CTC Breakdown Required When Shortlisted (Job Applicant, Form)
// While Shortlisted, Basic is required (Allowance and Benefits may be 0).
// Gross, CTC and the monthly figures update live as values are typed.
function ja_ctc_refresh(frm) {
    frm.set_df_property('custom_ctc_basic', 'reqd', frm.doc.custom_recruitment_status === 'Shortlisted' ? 1 : 0);
}
function ja_ctc_calc(frm) {
    const f = v => flt(v);
    const gross = f(frm.doc.custom_ctc_basic) + f(frm.doc.custom_ctc_allowance);
    const total = gross + f(frm.doc.custom_ctc_benefits);
    const vals = {
        custom_ctc_gross: gross, custom_ctc_total: total,
        custom_ctc_basic_monthly: f(frm.doc.custom_ctc_basic) / 12, custom_ctc_allowance_monthly: f(frm.doc.custom_ctc_allowance) / 12,
        custom_ctc_gross_monthly: gross / 12, custom_ctc_benefits_monthly: f(frm.doc.custom_ctc_benefits) / 12, custom_ctc_total_monthly: total / 12
    };
    Object.keys(vals).forEach(k => { if (flt(frm.doc[k]) !== flt(vals[k])) frm.set_value(k, vals[k]); });
    const agreed = f(frm.doc.custom_agreed_salary);
    const wrap = frm.fields_dict.custom_ctc_total && frm.fields_dict.custom_ctc_total.$wrapper;
    if (wrap) {
        wrap.find('.ja-ctc-hint').remove();
        if (agreed && total && Math.abs(total - agreed) > 0.5) {
            wrap.append('<div class="ja-ctc-hint" style="color:#b45309;font-size:12px;margin-top:4px">Does not match the Agreed Salary (' + format_currency(agreed, 'USD') + ').</div>');
        } else if (agreed && total) {
            wrap.append('<div class="ja-ctc-hint" style="color:#16a34a;font-size:12px;margin-top:4px">Matches the Agreed Salary.</div>');
        }
    }
}
frappe.ui.form.on('Job Applicant', {
    refresh(frm) { ja_ctc_refresh(frm); ja_ctc_calc(frm); },
    custom_recruitment_status: ja_ctc_refresh,
    custom_ctc_basic: ja_ctc_calc,
    custom_ctc_allowance: ja_ctc_calc,
    custom_ctc_benefits: ja_ctc_calc,
    custom_agreed_salary: ja_ctc_calc
});
