// VFQ HR desk navigation (loaded on every desk page via app_include_js).
//
// Users without System Manager never stay on the apps desktop: they are taken straight into
// the first VFQ HR workspace their roles allow (e.g. Self Service Portal or HR). The list of
// allowed workspaces comes from the server (boot `app_data` dock, already permission-filtered),
// so no role is hard-coded here. System Managers keep the normal desktop.
(function () {
	function restricted() {
		return !!(frappe.boot && frappe.boot.vfq_hr_only);
	}

	function on_desktop() {
		var path = (window.location.pathname || "").replace(/\/+$/, "");
		if (path !== "/desk" && path !== "/app") return false;
		var route = frappe.get_route ? frappe.get_route() : [];
		return !route.length || !route[0] || route[0] === "desktop";
	}

	function allowed_workspaces() {
		var app = (frappe.boot.app_data || []).find(function (a) {
			return a.app_name === "vfq_hr";
		});
		return ((app && app.dock) || [])
			.filter(function (e) {
				return e.link_type === "Workspace";
			})
			.map(function (e) {
				return e.link_to;
			});
	}

	// The app's own workspaces (from boot) that this user may NOT open, e.g. "HR" for an employee.
	function on_blocked_vfq_workspace() {
		var route = frappe.get_route ? frappe.get_route() : [];
		if (route[0] !== "Workspaces" || !route[1]) return false;
		var all = frappe.boot.vfq_hr_workspaces || [];
		return all.indexOf(route[1]) !== -1 && allowed_workspaces().indexOf(route[1]) === -1;
	}

	function landing_route() {
		try {
			var app = (frappe.boot.app_data || []).find(function (a) {
				return a.app_name === "vfq_hr";
			});
			var dock = (app && app.dock) || [];
			for (var i = 0; i < dock.length; i++) {
				var e = dock[i];
				if (e.link_type !== "Workspace" || !(frappe.ui.sidebar_item && frappe.ui.sidebar_item.get_route)) continue;
				var r = frappe.ui.sidebar_item.get_route(
					{ type: "Link", link_type: "Workspace", link_to: e.link_to, url: e.url },
					false
				);
				if (r) return r;
			}
		} catch (err) {
			// fall through to the default route
		}
		return frappe.boot.vfq_hr_route || "/app/hr";
	}

	var busy = false;
	function redirect_if_needed() {
		if (busy || !restricted() || !(on_desktop() || on_blocked_vfq_workspace())) return;
		busy = true;
		frappe.set_route(landing_route());
		setTimeout(function () {
			busy = false;
		}, 1000);
	}

	if (frappe.boot && frappe.boot.vfq_hr_brand_color) {
		document.documentElement.style.setProperty("--vfq-brand", frappe.boot.vfq_hr_brand_color);
	}

	$(document).on("page-change", redirect_if_needed);
	if (frappe.router && frappe.router.on) frappe.router.on("change", redirect_if_needed);
	$(redirect_if_needed);
})();
