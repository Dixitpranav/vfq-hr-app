# Copyright (c) 2026, ERPion
# License: MIT
"""Static checks that run on any bench: every shipped script compiles and every hook target exists."""

import json
import os

import frappe
from frappe.tests.utils import FrappeTestCase

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestVFQHRPackage(FrappeTestCase):
	def test_server_scripts_compile(self):
		with open(os.path.join(APP, "server_scripts", "registry.json")) as f:
			reg = json.load(f)
		for e in reg:
			path = os.path.join(APP, "server_scripts", "scripts", e["file"])
			from vfq_hr.runner import _restricted_compile

			with open(path) as fh:
				_restricted_compile(fh.read(), path)

	def test_hook_targets_resolve(self):
		hooks = frappe.get_hooks(app_name="vfq_hr")
		for dt, events in (hooks.get("doc_events") or {}).items():
			for fn in events.values():
				for f in fn if isinstance(fn, list) else [fn]:
					frappe.get_attr(f)
		for target in (hooks.get("override_whitelisted_methods") or {}).values():
			for t in target if isinstance(target, list) else [target]:
				frappe.get_attr(t)

	def test_reports_installed(self):
		with open(os.path.join(APP, "tools", "manifest.json")) as f:
			m = json.load(f)
		for r in m["reports"]:
			self.assertTrue(frappe.db.exists("Report", r), r)
