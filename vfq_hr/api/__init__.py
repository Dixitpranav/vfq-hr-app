# Auto-generated: whitelisted endpoints backed by the site's API Server Scripts.
# The original short method names are kept via override_whitelisted_methods in hooks.py.
import frappe

from vfq_hr.runner import run_api


@frappe.whitelist()
def activate_employee(*args, **kwargs):
	return run_api('Employee - Activate')


@frappe.whitelist()
def send_coi_form(*args, **kwargs):
	return run_api('Employee - Send COI Form')


@frappe.whitelist()
def bulk_create_performance_reviews(*args, **kwargs):
	return run_api('Bulk Create Performance Reviews')


@frappe.whitelist()
def get_review_access(*args, **kwargs):
	return run_api('Review Access - Relationship Lookup')


@frappe.whitelist()
def get_my_resignation_defaults(*args, **kwargs):
	return run_api('Employee Exit - Portal Resignation Defaults')


@frappe.whitelist()
def submit_portal_resignation(*args, **kwargs):
	return run_api('Submit Portal Resignation')


@frappe.whitelist()
def sync_self_service_user_permissions(*args, **kwargs):
	return run_api('Sync Self Service User Permissions (API)')


@frappe.whitelist()
def save_cxo_send_back_reason(*args, **kwargs):
	return run_api('CXO Hiring Approval - Save Send Back Reason')


@frappe.whitelist()
def get_cxo_function_shortlist(*args, **kwargs):
	return run_api('CXO Hiring Approval - Get Shortlisted Count')


@frappe.whitelist()
def request_workforce_plan_send_back(*args, **kwargs):
	return run_api('Workforce Plan - Request Send Back')


@frappe.whitelist()
def assign_leave_policy_for_employee(*args, **kwargs):
	return run_api('Assign Leave Policy for Employee')


@frappe.whitelist()
def fetch_existing_cost_for_role(*args, **kwargs):
	return run_api('Fetch Existing Cost for Role')
