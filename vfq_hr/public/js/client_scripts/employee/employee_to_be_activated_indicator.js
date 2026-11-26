// Client Script: Employee - To Be Activated Indicator (Employee, List)
(function () {
  const s = frappe.listview_settings["Employee"] = frappe.listview_settings["Employee"] || {};
  s.add_fields = (s.add_fields || []).concat(["custom_activation_status"]);
  const orig = s.get_indicator;
  s.get_indicator = function (doc) {
    if (doc.custom_activation_status === "To be activated") return [__("To be activated"), "orange", "custom_activation_status,=,To be activated"];
    if (orig) return orig(doc);
    const c = { Active: "green", Inactive: "red", Suspended: "orange", Left: "gray" };
    return [__(doc.status), c[doc.status] || "gray", "status,=," + doc.status];
  };
})();
