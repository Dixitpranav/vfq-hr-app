"""Boot-time navigation for VFQ HR.

Users who are not System Managers should only ever see the VFQ HR app: on the apps screen,
in the app dock and as their landing page. Other apps (Frappe HR, ERPNext, Framework) keep
working underneath, because the VFQ flow uses their doctypes, but their tiles and docks are
hidden for these users.

This runs as a `boot_session` hook, after Frappe has built the boot data, so it only trims
what is shown. It never changes roles, permissions or another app's records, which keeps it
safe across Frappe / ERPNext / HRMS upgrades.
"""

import frappe

APP = "vfq_hr"
FULL_ACCESS_ROLES = {"System Manager", "Administrator"}


def _is_restricted_user():
	user = frappe.session.user
	if user in ("Administrator", "Guest"):
		return False
	return not (FULL_ACCESS_ROLES & set(frappe.get_roles(user)))


def _vfq_route():
	major = int(frappe.__version__.split(".")[0])
	return ("/desk" if major >= 16 else "/app") + "/hr"


def boot_session(bootinfo):
	if not _is_restricted_user():
		return
	try:
		_trim_v16_app_data(bootinfo)
		_trim_v15_apps_data(bootinfo)
		bootinfo.vfq_hr_only = 1
		bootinfo.vfq_hr_route = _vfq_route()
	except Exception:
		# Navigation trimming must never break the desk: fall back to the standard boot.
		frappe.log_error(title="VFQ HR boot_session")


def _trim_v16_app_data(bootinfo):
	"""v16: `app_data` drives the apps screen and the dock."""
	app_data = bootinfo.get("app_data")
	if not app_data:
		return
	for app in app_data:
		if app.get("app_name") == APP:
			app["on_apps_screen"] = True
			continue
		# Keep the entry (titles are used for labels) but hide the tile and the dock.
		app["on_apps_screen"] = False
		app["dock"] = []


def _trim_v15_apps_data(bootinfo):
	"""v15: `apps_data.apps` drives the apps screen and the app switcher."""
	apps_data = bootinfo.get("apps_data")
	if not apps_data or not isinstance(apps_data, dict):
		return
	apps = [a for a in (apps_data.get("apps") or []) if a.get("name") == APP]
	if apps:
		apps_data["apps"] = apps
		apps_data["default_path"] = apps[0].get("route") or _vfq_route()
