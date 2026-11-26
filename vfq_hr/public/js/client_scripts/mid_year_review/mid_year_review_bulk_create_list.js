// Client Script: Mid-Year Review - Bulk Create (List) (Mid-Year Review, List)
// HR-only "Bulk Create" on the Mid-Year Review list: pick vendors and/or projects, preview who is eligible, create Draft reviews.
(function () {
  var DT = "Mid-Year Review";
  var IS_MID = true;
  frappe.listview_settings[DT] = frappe.listview_settings[DT] || {};
  var settings = frappe.listview_settings[DT];
  var prevOnload = settings.onload;
  settings.onload = function (listview) {
    if (prevOnload) prevOnload(listview);
    if (!frappe.user.has_role(["HR User", "HR Manager"])) return;
    listview.page.add_inner_button(__("Bulk Create Reviews"), function () { openBulkDialog(listview); });
  };

  function esc(s) { return frappe.utils.escape_html(s == null ? "" : String(s)); }

  function openBulkDialog(listview) {
    var yearNow = new Date().getFullYear();
    var fields = [];
    if (IS_MID) {
      var yrOpts = (frappe.meta.get_docfield(DT, "review_year") || {}).options || "";
      fields.push({ fieldname: "review_period", label: "Review Period", fieldtype: "Select", options: "\nH1\nH2", reqd: 1 });
      fields.push({ fieldtype: "Column Break" });
      fields.push({ fieldname: "review_year", label: "Review Year", fieldtype: "Select", options: yrOpts, reqd: 1, default: String(yearNow) });
    } else {
      fields.push({ fieldname: "review_year", label: "Review Year", fieldtype: "Int", reqd: 1, default: yearNow });
    }
    fields.push({ fieldtype: "Section Break", label: "Choose employees by" });
    fields.push({ fieldname: "vendors", label: "Vendors", fieldtype: "MultiSelectList", options: "Supplier",
      get_data: function (txt) { return frappe.db.get_link_options("Supplier", txt); } });
    fields.push({ fieldtype: "Column Break" });
    fields.push({ fieldname: "projects", label: "Projects", fieldtype: "MultiSelectList", options: "Project",
      get_data: function (txt) { return frappe.db.get_link_options("Project", txt); } });
    fields.push({ fieldtype: "Section Break" });
    fields.push({ fieldname: "rules", fieldtype: "HTML", options:
      '<div class="text-muted small">Eligible employees are active, joined at least 6 months ago, have a <b>submitted</b> Probation Review, no Probation Review or extension still in progress, a Confirmed status, and no review for the same period yet. If you pick both vendors and projects, an employee must match both.</div>' });
    fields.push({ fieldname: "results", fieldtype: "HTML" });

    var d = new frappe.ui.Dialog({
      title: __("Bulk Create {0}s", [DT]),
      size: "extra-large",
      fields: fields,
      primary_action_label: __("Create Selected Reviews"),
      primary_action: function () { createSelected(d, listview); },
      secondary_action_label: __("Find Employees"),
      secondary_action: function () { preview(d); }
    });
    d.show();
  }

  function args(d) {
    var v = d.get_values(true) || {};
    return {
      review_type: DT,
      review_period: v.review_period || "",
      review_year: v.review_year || "",
      vendors: JSON.stringify(v.vendors || []),
      projects: JSON.stringify(v.projects || [])
    };
  }

  function preview(d) {
    var a = args(d);
    a.action = "preview";
    frappe.call({ method: "bulk_create_performance_reviews", args: a, freeze: true, freeze_message: __("Checking employees...") }).then(function (r) {
      var rows = (r.message && r.message.rows) || [];
      var ok = rows.filter(function (x) { return x.eligible; });
      var no = rows.filter(function (x) { return !x.eligible; });
      var h = '<div style="margin-top:10px"><b>' + ok.length + '</b> eligible, <b>' + no.length + '</b> not eligible, out of ' + rows.length + ' matching employees.</div>';
      if (ok.length) {
        h += '<table class="table table-bordered table-sm" style="margin-top:8px"><thead><tr><th style="width:32px"><input type="checkbox" class="bulk-all" checked></th><th>Employee</th><th>Name</th><th>Vendor</th><th>Project</th><th>Joined</th></tr></thead><tbody>';
        ok.forEach(function (x) {
          h += '<tr><td><input type="checkbox" class="bulk-emp" data-emp="' + esc(x.employee) + '" checked></td><td>' + esc(x.employee) + '</td><td>' + esc(x.employee_name) + '</td><td>' + esc(x.vendor) + '</td><td>' + esc(x.project) + '</td><td>' + esc(frappe.datetime.str_to_user(x.date_of_joining)) + '</td></tr>';
        });
        h += '</tbody></table>';
      }
      if (no.length) {
        h += '<details style="margin-top:8px"><summary class="text-muted">Not eligible (' + no.length + ') – click to see why</summary><table class="table table-sm" style="margin-top:6px"><thead><tr><th>Employee</th><th>Name</th><th>Joined</th><th>Reason</th></tr></thead><tbody>';
        no.forEach(function (x) {
          h += '<tr class="text-muted"><td>' + esc(x.employee) + '</td><td>' + esc(x.employee_name) + '</td><td>' + esc(frappe.datetime.str_to_user(x.date_of_joining)) + '</td><td>' + esc(x.reasons.join("; ")) + '</td></tr>';
        });
        h += '</tbody></table></details>';
      }
      var wrap = d.fields_dict.results.$wrapper;
      wrap.html(h);
      wrap.find(".bulk-all").on("change", function () { wrap.find(".bulk-emp").prop("checked", this.checked); });
    });
  }

  function createSelected(d, listview) {
    var wrap = d.fields_dict.results.$wrapper;
    var chosen = [];
    wrap.find(".bulk-emp:checked").each(function () { chosen.push($(this).attr("data-emp")); });
    if (!chosen.length) {
      frappe.msgprint(__("Click Find Employees first, then tick the employees to create reviews for."));
      return;
    }
    frappe.confirm(__("Create {0} Draft {1}(s)?", [chosen.length, DT]), function () {
      var a = args(d);
      a.action = "create";
      a.employees = JSON.stringify(chosen);
      frappe.call({ method: "bulk_create_performance_reviews", args: a, freeze: true, freeze_message: __("Creating reviews...") }).then(function (r) {
        var m = r.message || {};
        var h = "<b>" + (m.created || []).length + "</b> review(s) created in Draft.";
        if ((m.created || []).length) {
          h += "<ul>" + m.created.map(function (c) { return '<li><a href="/app/' + frappe.router.slug(DT) + "/" + encodeURIComponent(c.name) + '">' + esc(c.name) + "</a> – " + esc(c.employee_name) + "</li>"; }).join("") + "</ul>";
        }
        if ((m.skipped || []).length) {
          h += "<b>" + m.skipped.length + "</b> skipped:<ul>" + m.skipped.map(function (s) { return "<li>" + esc(s.employee) + ": " + esc(s.reason) + "</li>"; }).join("") + "</ul>";
        }
        d.hide();
        frappe.msgprint({ title: __("Bulk Create Result"), message: h, indicator: (m.skipped || []).length ? "orange" : "green" });
        listview.refresh();
      });
    });
  }
})();
