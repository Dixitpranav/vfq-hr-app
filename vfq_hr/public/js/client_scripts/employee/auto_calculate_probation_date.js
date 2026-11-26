// Client Script: Auto calculate Probation date (Employee, Form)
frappe.ui.form.on("Employee", {
    date_of_joining: calculate_probation_end_date,
    custom_probation_months: calculate_probation_end_date
});

function calculate_probation_end_date(frm) {
    if (frm.doc.date_of_joining && frm.doc.custom_probation_months) {

        let probation_end = frappe.datetime.add_months(
            frm.doc.date_of_joining,
            cint(frm.doc.custom_probation_months)
        );

        frm.set_value("custom_probation_end_date", probation_end);
    }
}
