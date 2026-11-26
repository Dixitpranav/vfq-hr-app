// Client Script: Employee - Activation and HR Ops Controls (Employee, Form)
const EMP_CORE_FIELDS = ["company","designation","department","custom_role_classification","custom_hiring_type","custom_function","custom_sub_function","reports_to","branch","payroll_cost_center","job_applicant","custom_cxo_approval","custom_compa_ratio","employment_type","custom_variable_pay_type","custom_variable_pay_basis","custom_variable_pay_value","date_of_joining","custom_budget_plan","custom_budget_line","custom_work_country","custom_agreed_salary","ctc","custom_project","custom_vendor","status"];
frappe.ui.form.on("Employee", {
  refresh(frm) {
    const roles = frappe.user_roles || [];
    const isAdmin = frappe.session.user === "Administrator" || roles.includes("System Manager");
    const isHRM = isAdmin || roles.includes("HR Manager");
    const isOps = roles.includes("HR Ops") || roles.includes("HR Ops - VFQ Email");
    const pending = frm.doc.custom_activation_status === "To be activated";

    // HR Ops: core fields read-only once they hold a value
    if (isOps && !isHRM) {
      EMP_CORE_FIELDS.forEach(f => { if (frm.doc[f]) frm.set_df_property(f, "read_only", 1); });
    }
    if (pending && !isAdmin) frm.set_df_property("status", "read_only", 1);

    frm.set_df_property("company_email", "description", "Enter the VFQ email ID here once it is created. Saving an Active employee with this filled in creates the system user and links it automatically.");

    if (pending && !frm.is_new()) {
      frm.dashboard.set_headline_alert(__("Awaiting activation: HR Ops to verify the details, complete missing personal fields and click <b>Activate</b>."), "orange");
      if (isOps || isHRM) {
        frm.add_custom_button(__("Activate"), () => {
          if (frm.is_dirty()) { frappe.msgprint(__("Please save your changes first.")); return; }
          frappe.confirm(__("Activate {0}? A VFQ email request will be sent to the HR Ops - VFQ Email team.", [frm.doc.employee_name]), () => {
            frappe.call({ method: "activate_employee", args: { employee: frm.doc.name }, freeze: true, freeze_message: __("Activating…") })
              .then(r => { frappe.show_alert({ message: __("Employee activated. VFQ email request sent to {0} user(s).", [(r.message || {}).notified || 0]), indicator: "green" }); frm.reload_doc(); });
          });
        }).addClass("btn-primary");
      }
    }
    if (frm.doc.status === "Active" && !frm.doc.user_id && !frm.doc.company_email && (isOps || isHRM)) {
      frm.dashboard.set_headline_alert(__("Active. Next: enter the VFQ email ID in <b>Company Email</b> and save to create and link the system user."), "blue");
    }
  }
});
