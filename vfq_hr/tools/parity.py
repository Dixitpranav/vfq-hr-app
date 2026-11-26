# Copyright (c) 2026, ERPion
# License: MIT
"""Parity check: compares this site with the configuration VFQ HR is expected to deliver.

	bench --site <site> execute vfq_hr.tools.parity.run
	bench --site <site> execute vfq_hr.tools.parity.smoke_reports

`run` prints every missing or different item and returns a summary dict.
`smoke_reports` runs every VFQ HR report with empty filters and reports errors.
"""

import json
import os

import frappe

MANIFEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")


def _m():
	with open(MANIFEST) as f:
		return json.load(f)


def run():
	m = _m()
	issues = []

	def miss(kind, what):
		issues.append(f"MISSING {kind}: {what}")

	def diff(kind, what, expected, actual):
		issues.append(f"DIFFERENT {kind}: {what} expected={expected!r} actual={actual!r}")

	for dt in m["doctypes"]:
		if not frappe.db.exists("DocType", dt):
			miss("DocType", dt)
	for r in m["reports"]:
		if not frappe.db.exists("Report", r):
			miss("Report", r)
	for f in m["custom_fields"]:
		row = frappe.db.get_value("Custom Field", {"dt": f["dt"], "fieldname": f["fieldname"]}, ["fieldtype", "options"], as_dict=True)
		if not row:
			miss("Custom Field", f"{f['dt']}.{f['fieldname']}")
		elif row.fieldtype != f["fieldtype"]:
			diff("Custom Field type", f"{f['dt']}.{f['fieldname']}", f["fieldtype"], row.fieldtype)
	for p in m["property_setters"]:
		filters = {"doc_type": p["doc_type"], "property": p["property"]}
		filters["field_name"] = p["field_name"] or ("is", "not set")
		val = frappe.db.get_value("Property Setter", filters, "value")
		if val is None:
			miss("Property Setter", f"{p['doc_type']}.{p['field_name']}.{p['property']}")
		elif str(val) != str(p["value"]):
			diff("Property Setter", f"{p['doc_type']}.{p['field_name']}.{p['property']}", p["value"], val)
	for r in m["roles"]:
		if not frappe.db.exists("Role", r):
			miss("Role", r)
	for p in m["custom_docperm"]:
		if not frappe.db.exists("Custom DocPerm", {"parent": p["parent"], "role": p["role"], "permlevel": p["permlevel"]}):
			miss("Permission", f"{p['parent']} / {p['role']} / level {p['permlevel']}")
	for w in m["workflows"]:
		if not frappe.db.exists("Workflow", w["name"]):
			miss("Workflow", w["name"])
			continue
		wf = frappe.get_doc("Workflow", w["name"])
		if int(wf.is_active or 0) != int(w["is_active"] or 0):
			diff("Workflow active", w["name"], w["is_active"], wf.is_active)
		if len(wf.states) != w["states"] or len(wf.transitions) != w["transitions"]:
			diff("Workflow size", w["name"], (w["states"], w["transitions"]), (len(wf.states), len(wf.transitions)))
	for n in m["notifications"]:
		en = frappe.db.get_value("Notification", n["name"], "enabled")
		if en is None:
			miss("Notification", n["name"])
		elif int(en) != int(n["enabled"]):
			diff("Notification enabled", n["name"], n["enabled"], en)
	for w in m["workspaces"]:
		if not frappe.db.exists("Workspace", w["name"]):
			miss("Workspace", w["name"])
			continue
		ws = frappe.get_doc("Workspace", w["name"])
		sc = sorted(s.label for s in ws.shortcuts)
		cards = sorted(l.label for l in ws.links if l.type == "Card Break")
		if sc != w["shortcuts"]:
			diff("Workspace shortcuts", w["name"], len(w["shortcuts"]), len(sc))
		if cards != w["cards"]:
			diff("Workspace cards", w["name"], w["cards"], cards)
	for name in m["visibility"]["system_manager_only"]:
		if frappe.db.exists("Workspace", name):
			roles = frappe.get_all("Has Role", filters={"parent": name, "parenttype": "Workspace"}, pluck="role")
			if roles != ["System Manager"]:
				diff("Sidebar visibility", name, ["System Manager"], roles)
	for api in m["api_methods"]:
		target = (frappe.get_hooks("override_whitelisted_methods") or {}).get(api)
		if not target:
			miss("API method", api)
	for kind, key in (("Print Format", "print_formats"), ("Web Form", "web_forms"), ("Dashboard Chart", "dashboard_charts"), ("Number Card", "number_cards"), ("Dashboard", "dashboards")):
		for n in m[key]:
			if not frappe.db.exists(kind, n):
				miss(kind, n)

	if frappe.db.get_single_value("System Settings", "enable_scheduler") in (0, None):
		issues.append("NOTE: scheduler is disabled on this site; VFQ HR daily/monthly jobs will not run.")

	for line in issues:
		print(line)
	summary = {"issues": len(issues), "checked_from": m.get("generated_from", {}).get("site")}
	print("PARITY", "OK" if not issues else "ISSUES", json.dumps(summary))
	return summary


def smoke_reports():
	m = _m()
	failed = {}
	for r in m["reports"]:
		try:
			from frappe.desk.query_report import run as run_report

			run_report(r, filters={})
		except Exception as e:
			failed[r] = f"{type(e).__name__}: {e}"[:300]
	for k, v in failed.items():
		print("REPORT FAILED:", k, "->", v)
	print("REPORTS", len(m["reports"]) - len(failed), "ok,", len(failed), "failed")
	return failed
