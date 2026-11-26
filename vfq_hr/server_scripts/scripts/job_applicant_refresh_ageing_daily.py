# Server Script: Job Applicant - Refresh Ageing Daily
# Type: Scheduler Event | Frequency: Daily
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

today = frappe.utils.getdate(frappe.utils.nowdate())
for a in frappe.get_all("Job Applicant", filters={"custom_role_sharing_date": ["is", "set"], "custom_onboarded_date": ["is", "not set"]}, fields=["name", "custom_role_sharing_date"]):
    frappe.db.set_value("Job Applicant", a.name, "custom_ageing_days", frappe.utils.date_diff(today, frappe.utils.getdate(a.custom_role_sharing_date)), update_modified=False)
