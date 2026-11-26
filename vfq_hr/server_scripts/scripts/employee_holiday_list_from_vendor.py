# Server Script: Employee - Holiday List from Vendor
# Type: DocType Event | DocType: Employee | Event: Before Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# New employees get the holiday list of their vendor's country:
# the vendor's own Holiday List if set (e.g. India vendors), otherwise the Qatar list.
# Employees without a vendor also get the Qatar list. A list already chosen by HR is kept.
if not doc.holiday_list:
    hl = None
    if doc.get("custom_vendor"):
        hl = frappe.db.get_value("Supplier", doc.custom_vendor, "custom_holiday_list")
    if not hl:
        hl = "Qatar Public Holidays 2026-2027"
    if frappe.db.exists("Holiday List", hl):
        doc.holiday_list = hl
