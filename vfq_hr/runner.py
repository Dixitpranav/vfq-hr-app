# Copyright (c) 2026, ERPion
# License: MIT
"""Runs the VFQ HR business logic that was built as Frappe Server Scripts.

Each script lives verbatim in vfq_hr/server_scripts/scripts/*.py and is compiled and executed
exactly like a Frappe Server Script (RestrictedPython with Frappe's policy, and the globals from
frappe.utils.safe_exec.get_safe_globals), so its behaviour and sandbox are unchanged. Because the code ships inside the app, the site does not need
`server_script_enabled`, and nothing depends on Server Script records in the database.

Behaviour kept identical to Frappe's own Server Script runner:
- doc events: locals {"doc": doc}; db commit/rollback blocked; skipped during install/migrate
- permission query: locals {"user": user, "conditions": ""}; returns `conditions`
- API: runs with frappe.form_dict; the script sets frappe.response["message"]
- reports: locals {"filters": filters, "data": None, "result": None}
"""

import contextlib
import json
import os
from functools import lru_cache

import frappe

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(APP_DIR, "server_scripts")


@lru_cache(maxsize=1)
def _registry():
	with open(os.path.join(SCRIPTS_DIR, "registry.json")) as f:
		return json.load(f)


@lru_cache(maxsize=1)
def _index():
	doc_events, pq, api, sched = {}, {}, {}, {}
	for e in _registry():
		if e["type"] == "DocType Event":
			doc_events.setdefault((e["doctype"], e["method"]), []).append(e)
		elif e["type"] == "Permission Query":
			pq[e["doctype"]] = e
		elif e["type"] == "API":
			api[e["name"]] = e
		elif e["type"] == "Scheduler Event":
			sched[e["name"]] = e
	return doc_events, pq, api, sched


def _restricted_compile(src, filename):
	"""Compile exactly like Frappe compiles a Server Script (RestrictedPython + Frappe policy).

	This keeps Server Script semantics, e.g. reading a missing field returns None instead of
	raising, and the same sandbox rules apply.
	"""
	try:  # v16
		from frappe.utils.safe_exec import _compile_code

		return _compile_code(src, filename=filename)
	except ImportError:
		pass
	from RestrictedPython import compile_restricted

	try:  # v15
		from frappe.utils.safe_exec import FrappeTransformer

		return compile_restricted(src, filename=filename, policy=FrappeTransformer)
	except ImportError:
		return compile_restricted(src, filename=filename)


@lru_cache(maxsize=None)
def _compile_file(path):
	with open(path) as f:
		src = f.read()
	return _restricted_compile(src, "<serverscript>: " + os.path.basename(path))


def _script_code(entry):
	return _compile_file(os.path.join(SCRIPTS_DIR, "scripts", entry["file"]))


def _safe_globals(restrict_commit_rollback=False):
	from frappe.utils.safe_exec import get_safe_globals

	g = get_safe_globals()
	# Version-neutral helpers available to every VFQ HR script (see vfq_hr/compat.py).
	from vfq_hr import compat

	g["vfq_budget_header"] = compat.budget_header
	g["vfq_budget_accounts"] = compat.budget_accounts
	g["vfq_budget_covers_year"] = compat.budget_covers_year
	if restrict_commit_rollback:
		try:
			for key in ("commit", "rollback", "add_index"):
				g["frappe"]["db"].pop(key, None)
		except Exception:
			pass
	return g


def _flags():
	try:
		from frappe.utils.safe_exec import safe_exec_flags

		return safe_exec_flags()
	except Exception:
		return contextlib.nullcontext()


def _exec(code, _locals, restrict_commit_rollback=False):
	g = _safe_globals(restrict_commit_rollback)
	with _flags():
		exec(code, g, _locals)
	return _locals


# ------------------------------------------------------------------ doc events
def run_doc_event(doc, method=None):
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if getattr(frappe.flags, "vfq_hr_disable_logic", False):
		return
	doc_events, _, _, _ = _index()
	for entry in doc_events.get((doc.doctype, method), []):
		_exec(_script_code(entry), {"doc": doc}, restrict_commit_rollback=True)


# ------------------------------------------------------------ permission query
def run_permission_query(doctype, user=None):
	_, pq, _, _ = _index()
	entry = pq.get(doctype)
	if not entry:
		return ""
	loc = _exec(_script_code(entry), {"user": user or frappe.session.user, "conditions": "", "active_child_tables": []})
	return loc.get("conditions") or ""


# ------------------------------------------------------------------------ API
def run_api(name):
	_, _, api, _ = _index()
	_exec(_script_code(api[name]), {})
	# The script sets frappe.response["message"] itself, like a Server Script API.
	return None


# ------------------------------------------------------------------ scheduler
def run_scheduled(name):
	_, _, _, sched = _index()
	_exec(_script_code(sched[name]), {})


# -------------------------------------------------------------------- reports
def run_report_script(report_py_file, filters=None):
	folder = os.path.dirname(os.path.abspath(report_py_file))
	code = _compile_file(os.path.join(folder, "script.py"))
	loc = _exec(code, {"filters": frappe._dict(filters or {}), "data": None, "result": None})
	if loc.get("data"):
		return loc["data"]
	return [], loc.get("result") or []
