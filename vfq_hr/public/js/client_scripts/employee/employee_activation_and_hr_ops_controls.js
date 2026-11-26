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

    frm.set_df_property("company_email", "description", "Official VFQ email ID (domain must contain \"vodafone\", e.g. .qa, .com, .in). Required before Activate; on activation the system user is created and linked, and the COI form is emailed here.");

    if (pending && !frm.is_new()) {
      frm.dashboard.set_headline_alert(frm.doc.company_email
        ? __("Awaiting activation: HR Ops to verify the details, complete missing personal fields and click <b>Activate</b>. Activation emails the COI form to the employee.")
        : __("Awaiting activation: the <b>Official Email (VFQ)</b> must be filled in (domain containing \"vodafone\") before the employee can be activated."), "orange");
      if (isOps || isHRM) {
        frm.add_custom_button(__("Activate"), () => {
          if (frm.is_dirty()) { frappe.msgprint(__("Please save your changes first.")); return; }
          if (!frm.doc.company_email) { frappe.msgprint({ title: __("Official email required"), indicator: "orange", message: __("Enter the <b>Official Email (VFQ)</b> first (domain must contain \"vodafone\") and save.") }); frm.scroll_to_field("company_email"); return; }
          frappe.confirm(__("Activate {0}? The system user will be created for {1} and the COI form emailed to it.", [frm.doc.employee_name, frm.doc.company_email]), () => {
            frappe.call({ method: "activate_employee", args: { employee: frm.doc.name }, freeze: true, freeze_message: __("Activating…") })
              .then(r => { const m = r.message || {}; frappe.show_alert({ message: m.coi_status === "Sent" ? __("Employee activated. COI form emailed to {0}.", [frm.doc.company_email]) : __("Employee activated. COI email not sent: {0}", [m.coi_note || ""]), indicator: m.coi_status === "Sent" ? "green" : "orange" }, 10); frm.reload_doc(); });
          });
        }).addClass("btn-primary");
      }
    }
    if (frm.doc.status === "Active" && !frm.is_new() && (isOps || isHRM)) {
      const coi = frm.doc.custom_coi_status;
      if (coi === "Sent") frm.dashboard.set_headline_alert(__("COI form sent to {0} on {1}. Waiting for the signed copy by reply.", [frm.doc.custom_coi_sent_to, frappe.datetime.str_to_user(frm.doc.custom_coi_trigger_date)]), "blue");
      if (coi === "Sending Failed") frm.dashboard.set_headline_alert(__("COI email not sent: {0}", [frm.doc.custom_coi_note || ""]), "red");
      if (coi !== "Received") {
        frm.add_custom_button(coi === "Sent" || coi === "Sending Failed" ? __("Resend COI Form") : __("Send COI Form"), () => {
          frappe.call({ method: "send_coi_form", args: { employee: frm.doc.name }, freeze: true })
            .then(r => { const m = r.message || {}; frappe.show_alert({ message: m.note || m.status, indicator: m.status === "Sent" ? "green" : "orange" }, 10); frm.reload_doc(); });
        }, __("COI"));
      }
    }
  }
});
