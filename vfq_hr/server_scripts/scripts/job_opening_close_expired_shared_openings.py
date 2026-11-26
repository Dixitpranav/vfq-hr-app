# Server Script: Job Opening - Close Expired Shared Openings
# Type: Scheduler Event | Frequency: Daily
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

today = frappe.utils.getdate(frappe.utils.nowdate())
for j in frappe.get_all("Job Opening", filters={"status": "Open & To be shared with vendor", "closes_on": ["<", today]}, pluck="name"):
    frappe.db.set_value("Job Opening", j, {"status": "Closed", "closed_on": today})
