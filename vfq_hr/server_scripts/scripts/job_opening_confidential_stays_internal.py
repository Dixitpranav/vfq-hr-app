# Server Script: Job Opening - Confidential Stays Internal
# Type: DocType Event | DocType: Job Opening | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

if frappe.utils.cint(doc.get("custom_confidential_hiring")):
    if doc.get("custom_vendor") or frappe.utils.cint(doc.get("custom_pushed_to_vendor")):
        frappe.throw("This is a confidential hiring position. It stays internal and cannot have a vendor or be pushed to a vendor. Clear the vendor and the Pushed to Vendor box.", title="Confidential Hiring")
