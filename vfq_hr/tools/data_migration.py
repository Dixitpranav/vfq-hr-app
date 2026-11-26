"""One-off data migration into a VFQ HR site (System Manager only).

Moving existing records (for example employees from an older site) must not re-run the
hiring flow's business rules: those would mark every employee "To be activated", email HR
Ops once per record, create probation reviews and grant self-service permissions again.
`import_docs` inserts records with the VFQ HR rules switched off for that request only
(`frappe.flags.vfq_hr_disable_logic`, honoured by vfq_hr.runner) and with outgoing email
muted. Standard Frappe / ERPNext / HRMS validation still runs.

Called from the browser or a script:
    frappe.call("vfq_hr.tools.data_migration.import_docs", {docs: [...], ignore_links: 0})
"""

import json

import frappe

ALLOWED_DOCTYPES = None  # any doctype; the caller must be a System Manager


def _check_permission():
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Only a System Manager can run the VFQ HR data migration.", frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def import_docs(docs, ignore_links=0, update_existing=0):
	"""Insert (or optionally update) records with VFQ HR rules and email switched off.

	Returns one result per record: {"name", "status": "inserted|updated|exists|error", "error"}.
	Each record is committed on its own so one failure does not undo the rest.
	"""
	_check_permission()
	if isinstance(docs, str):
		docs = json.loads(docs)
	ignore_links = frappe.utils.cint(ignore_links)
	update_existing = frappe.utils.cint(update_existing)

	frappe.flags.vfq_hr_disable_logic = True
	frappe.flags.mute_emails = True
	results = []
	try:
		for rec in docs or []:
			name = rec.get("name")
			doctype = rec.get("doctype")
			try:
				if name and frappe.db.exists(doctype, name):
					if not update_existing:
						results.append({"name": name, "status": "exists"})
						continue
					doc = frappe.get_doc(doctype, name)
					doc.update({k: v for k, v in rec.items() if k not in ("name", "doctype")})
					doc.flags.ignore_links = bool(ignore_links)
					doc.save(ignore_permissions=True)
					status = "updated"
				else:
					doc = frappe.get_doc(rec)
					doc.flags.ignore_links = bool(ignore_links)
					doc.insert(ignore_permissions=True, set_name=name)
					status = "inserted"
				frappe.db.commit()
				results.append({"name": doc.name, "status": status})
			except Exception as e:
				frappe.db.rollback()
				msg = str(e) or e.__class__.__name__
				results.append({"name": name, "status": "error", "error": frappe.utils.strip_html(msg)[:300]})
				frappe.clear_messages()
	finally:
		frappe.flags.vfq_hr_disable_logic = False
		frappe.flags.mute_emails = False
	return results


@frappe.whitelist(methods=["POST"])
def set_values(doctype, values):
	"""Set fields directly (no rules, no emails) — e.g. status/user links after an import.

	values: [{"name": ..., "fields": {...}}]
	"""
	_check_permission()
	if isinstance(values, str):
		values = json.loads(values)
	done = 0
	for row in values or []:
		if frappe.db.exists(doctype, row.get("name")):
			frappe.db.set_value(doctype, row["name"], row.get("fields") or {}, update_modified=False)
			done += 1
	frappe.db.commit()
	return {"updated": done}
