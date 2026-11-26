"""Portal branding, filled in by the customer on the Company record (nothing hard-coded).

Company > "Portal Branding" section:
  custom_portal_title      shown above the sign-in card (falls back to the company name)
  custom_portal_tagline    optional second line under the title
  custom_login_note        optional note under the sign-in card
  custom_portal_logo       optional logo on the sign-in card (falls back to the VFQ HR icon)
  custom_brand_color       theme colour for the sign-in page and desk desktop (default red)

The company used is the site's default company (Global Defaults), else the first company that
has branding filled in.
"""

import json

import frappe

DEFAULT_COLOR = "#E60000"
SIGN_IN_PATHS = {"login", "update-password"}
FIELDS = ["custom_portal_title", "custom_portal_tagline", "custom_login_note", "custom_portal_logo", "custom_brand_color"]


def branding_fields():
	return [
		{"fieldname": "custom_portal_branding_section", "label": "Portal Branding", "fieldtype": "Section Break",
		 "insert_after": "default_holiday_list", "collapsible": 1},
		{"fieldname": "custom_portal_title", "label": "Portal Title", "fieldtype": "Data", "insert_after": "custom_portal_branding_section",
		 "description": "Shown above the sign-in box. Leave empty to use the company name."},
		{"fieldname": "custom_portal_tagline", "label": "Portal Tagline", "fieldtype": "Data", "insert_after": "custom_portal_title"},
		{"fieldname": "custom_login_note", "label": "Sign-in Page Note", "fieldtype": "Small Text", "insert_after": "custom_portal_tagline",
		 "description": "Optional line under the sign-in box, e.g. who to contact for access."},
		{"fieldname": "custom_portal_branding_cb", "fieldtype": "Column Break", "insert_after": "custom_login_note"},
		{"fieldname": "custom_portal_logo", "label": "Portal Logo", "fieldtype": "Attach Image", "insert_after": "custom_portal_branding_cb"},
		{"fieldname": "custom_brand_color", "label": "Brand Colour", "fieldtype": "Color", "insert_after": "custom_portal_logo",
		 "default": DEFAULT_COLOR, "description": "Theme colour of the sign-in page and the apps desktop."},
	]


def ensure_branding_fields():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields({"Company": branding_fields()}, ignore_validate=True, update=True)


def get_branding():
	"""Branding of the portal company, cached; safe for Guest pages."""
	def _load():
		meta = frappe.get_meta("Company")
		fields = [f for f in FIELDS if meta.has_field(f)]
		company = frappe.db.get_single_value("Global Defaults", "default_company")
		if not company or not frappe.db.exists("Company", company):
			company = None
			if "custom_portal_title" in fields:
				company = frappe.db.get_value("Company", {"custom_portal_title": ["is", "set"]}, "name")
			company = company or frappe.db.get_value("Company", {}, "name", order_by="creation asc")
		values = frappe.db.get_value("Company", company, fields, as_dict=True) if (company and fields) else {}
		values = values or {}
		return {
			"title": values.get("custom_portal_title") or company or "",
			"tagline": values.get("custom_portal_tagline") or "",
			"note": values.get("custom_login_note") or "",
			"logo": values.get("custom_portal_logo") or "/assets/vfq_hr/images/vfq_hr_logo.svg",
			"color": values.get("custom_brand_color") or DEFAULT_COLOR,
		}

	return frappe.cache.get_value("vfq_hr_branding", _load)


def clear_branding_cache(doc=None, method=None):
	frappe.cache.delete_value("vfq_hr_branding")


def update_website_context(context):
	"""Add the company's branding to the sign-in pages (rendered as text, never as HTML)."""
	path = (getattr(frappe.local, "path", None) or context.get("pathname") or context.get("path") or "").strip("/")
	if path not in SIGN_IN_PATHS:
		return
	try:
		data = json.dumps(get_branding()).replace("</", "<\\/")
	except Exception:
		frappe.log_error(title="VFQ HR branding")
		return
	script = "<script>window.vfq_hr_branding = " + data + ";</script>" + '<script src="/assets/vfq_hr/js/vfq_hr_login.js"></script>'
	context["body_include"] = (context.get("body_include") or "") + script


def boot_branding(bootinfo):
	try:
		bootinfo.vfq_hr_brand_color = get_branding().get("color")
	except Exception:
		pass
