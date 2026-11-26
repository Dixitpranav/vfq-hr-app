# Copyright (c) 2026, ERPion
# License: MIT
"""Install and upgrade-protection steps for VFQ HR.

after_install: seed the flow's masters (insert-only, never overwrites), apply HR Settings,
               apply sidebar visibility.
after_migrate: re-apply sidebar visibility so ERPNext/Frappe HR updates never bring back
               hidden menus. (Fixtures re-apply fields, permissions, workflows, notifications
               and workspaces on every migrate.)
"""

import json
import os

import frappe

SEED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup", "seed_data")

# Insert order matters (links between masters).
SEED_ORDER = [
	("Function", "function.json"),
	("Employment Type", "employment_type.json"),
	("Job Applicant Source", "job_applicant_source.json"),
	("Designation", "designation.json"),
	("Exit Reason", "exit_reason.json"),
	("KRA Category", "kra_category.json"),
	("Leave Type", "leave_type.json"),
	("Leave Policy", "leave_policy.json"),
	("Leave Policy Mapping", "leave_policy_mapping.json"),
	("Interview Type", "interview_type.json"),
	("Interview Round", "interview_round.json"),
	("Job Opening Template", "job_opening_template.json"),
]


def _load(fname):
	path = os.path.join(SEED_DIR, fname)
	if not os.path.exists(path):
		return None
	with open(path) as f:
		return json.load(f)


def after_install():
	result = seed_masters()
	apply_hr_settings()
	ensure_coi_setup()
	apply_workspace_visibility()
	frappe.db.commit()
	print("VFQ HR installed. Seed summary:", json.dumps(result))


def after_migrate():
	ensure_coi_setup()
	ensure_workspaces()
	apply_workspace_visibility()
	frappe.clear_cache()


# ----------------------------------------------------------------- masters
def seed_masters():
	summary = {}
	for doctype, fname in SEED_ORDER:
		if not frappe.db.exists("DocType", doctype):
			summary[doctype] = "doctype missing"
			continue
		records = _load(fname) or []
		ok = skipped = failed = 0
		for rec in records:
			name = rec.get("name")
			if name and frappe.db.exists(doctype, name):
				skipped += 1
				continue
			try:
				doc = frappe.get_doc(rec)
				docstatus = rec.get("docstatus") or 0
				doc.docstatus = 0
				doc.insert(ignore_permissions=True, set_name=name)
				if docstatus == 1:
					doc.submit()
				ok += 1
			except Exception:
				frappe.db.rollback()
				failed += 1
				frappe.log_error(title=f"VFQ HR seed failed: {doctype} {name}")
		summary[doctype] = {"inserted": ok, "existing": skipped, "failed": failed}
	return summary


def create_departments(company):
	"""Create the flow's department structure for a company.

	bench --site <site> execute vfq_hr.install.create_departments --kwargs '{"company": "Vodafone Qatar"}'
	"""
	abbr = frappe.db.get_value("Company", company, "abbr")
	if not abbr:
		frappe.throw(f"Company {company} not found")
	created = 0
	for d in _load("department.json") or []:
		name = f"{d['department_name']} - {abbr}"
		if frappe.db.exists("Department", name):
			continue
		parent = "All Departments" if d["parent"] == "All Departments" else f"{d['parent']} - {abbr}"
		if not frappe.db.exists("Department", parent):
			parent = "All Departments"
		doc = frappe.get_doc({
			"doctype": "Department",
			"department_name": d["department_name"],
			"company": company,
			"parent_department": parent,
			"is_group": d.get("is_group") or 0,
		})
		for f in ("custom_function", "custom_sub_function"):
			if d.get(f) and frappe.db.exists("Function", d[f]) and doc.meta.has_field(f):
				doc.set(f, d[f])
		doc.insert(ignore_permissions=True)
		created += 1
	frappe.db.commit()
	return {"created": created}


# --------------------------------------------------------------- COI setup
COI_TEMPLATE = "Employee COI Declaration"
COI_FORM_NAME = "VFQ COI Declaration Form (blank).docx"


def _ensure_folder(name, parent="Home"):
	path = f"{parent}/{name}"
	if not frappe.db.exists("File", path):
		frappe.get_doc({"doctype": "File", "file_name": name, "is_folder": 1, "folder": parent}).insert(ignore_permissions=True)
	return path


def ensure_coi_setup():
	"""Insert-only: folders, COI email template, blank COI form and HR Settings defaults.

	Never overwrites what HR has edited, so upgrades keep their changes.
	"""
	_ensure_folder("COI")
	templates_folder = _ensure_folder("COI Templates")

	if not frappe.db.exists("Email Template", COI_TEMPLATE):
		rec = _load("email_template_coi.json")
		if rec:
			frappe.get_doc(rec).insert(ignore_permissions=True)

	if not frappe.get_meta("HR Settings").has_field("custom_coi_form_template"):
		return
	values = {}
	if not frappe.db.get_single_value("HR Settings", "custom_official_email_domain_keyword"):
		values["custom_official_email_domain_keyword"] = "vodafone"
	if not frappe.db.get_single_value("HR Settings", "custom_coi_email_template"):
		values["custom_coi_email_template"] = COI_TEMPLATE
	if not frappe.db.get_single_value("HR Settings", "custom_coi_folder"):
		values["custom_coi_folder"] = "Home/COI"
	if not frappe.db.get_single_value("HR Settings", "custom_coi_form_template"):
		path = os.path.join(SEED_DIR, "coi_form_blank.docx")
		if os.path.exists(path):
			with open(path, "rb") as f:
				content = f.read()
			fdoc = frappe.get_doc({
				"doctype": "File",
				"file_name": COI_FORM_NAME,
				"folder": templates_folder,
				"is_private": 1,
				"content": content,
			})
			fdoc.insert(ignore_permissions=True)
			values["custom_coi_form_template"] = fdoc.file_url
	for key, value in values.items():
		frappe.db.set_single_value("HR Settings", key, value)


# ------------------------------------------------------------- HR Settings
def apply_hr_settings():
	data = _load("hr_settings.json") or {}
	if not data:
		return
	settings = frappe.get_single("HR Settings")
	for key, value in data.items():
		if key in ("name", "doctype", "docstatus", "idx") or isinstance(value, list):
			continue
		df = settings.meta.get_field(key)
		if not df:
			continue
		if df.fieldtype == "Link" and value and not frappe.db.exists(df.options, value):
			continue
		settings.set(key, value)
	settings.flags.ignore_mandatory = True
	settings.flags.ignore_permissions = True
	settings.save()


# ------------------------------------------------------- sidebar visibility
OWN_MODULE = "VFQ HR"
WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vfq_hr", "workspace")


def has_app_permission():
	"""VFQ HR tile on the apps screen: any logged-in desk user."""
	return frappe.session.user != "Guest"


def ensure_workspaces():
	"""Make sure the VFQ HR pages are the app's own records.

	On v15 Frappe HR also ships a page called "HR"; if an HR update ever replaces ours, re-import it.
	"""
	from frappe.modules.import_file import import_file_by_path

	if not os.path.isdir(WORKSPACE_DIR):
		return
	for folder in sorted(os.listdir(WORKSPACE_DIR)):
		path = os.path.join(WORKSPACE_DIR, folder, folder + ".json")
		if not os.path.exists(path):
			continue
		with open(path) as f:
			name = json.load(f)["name"]
		if frappe.db.get_value("Workspace", name, "module") != OWN_MODULE:
			import_file_by_path(path, force=True, ignore_version=True)


def _restrict_roles_direct(parent, parenttype, roles=("System Manager",)):
	current = frappe.get_all("Has Role", filters={"parent": parent, "parenttype": parenttype}, pluck="role")
	if sorted(current) == sorted(roles):
		return
	frappe.db.delete("Has Role", {"parent": parent, "parenttype": parenttype})
	for i, role in enumerate(roles, 1):
		frappe.get_doc({
			"doctype": "Has Role",
			"parent": parent,
			"parenttype": parenttype,
			"parentfield": "roles",
			"role": role,
			"idx": i,
		}).db_insert()


def apply_workspace_visibility():
	"""Only System Manager sees navigation outside VFQ HR (re-applied after every migrate)."""
	cfg = _load("workspace_visibility.json") or {}
	own = set(frappe.get_all("Workspace", filters={"module": OWN_MODULE}, pluck="name"))

	if frappe.db.exists("DocType", "Custom Workspace"):
		# v16: use the site-level override layer, which app updates never overwrite.
		from frappe.desk.doctype.custom_workspace.custom_workspace import upsert_settings_customization

		others = frappe.get_all("Workspace", filters={"public": 1}, pluck="name")
		for name in others:
			if name in own:
				continue
			try:
				upsert_settings_customization(name, roles=["System Manager"])
			except Exception:
				frappe.log_error(title=f"VFQ HR: could not restrict workspace {name}")
	else:
		# v15: hide the same pages as the source site and restrict the HR duplicates / Payroll.
		for name in cfg.get("hidden", []):
			if frappe.db.exists("Workspace", name) and name not in own:
				frappe.db.set_value("Workspace", name, "is_hidden", 1, update_modified=False)
		for name in cfg.get("system_manager_only", []):
			if frappe.db.exists("Workspace", name) and name not in own:
				_restrict_roles_direct(name, "Workspace")

	# v16 desktop grid: icons of other apps are System Manager only.
	if frappe.db.exists("DocType", "Desktop Icon") and frappe.get_meta("Desktop Icon").has_field("roles"):
		icons = frappe.get_all("Desktop Icon", filters=[["app", "is", "set"], ["app", "!=", "vfq_hr"]], pluck="name")
		for icon in icons:
			_restrict_roles_direct(icon, "Desktop Icon")
