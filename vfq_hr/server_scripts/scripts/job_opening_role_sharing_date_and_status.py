# Server Script: Job Opening - Role Sharing Date and Status
# Type: DocType Event | DocType: Job Opening | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

shared_status = "Open & To be shared with vendor"
confidential = frappe.utils.cint(doc.get("custom_confidential_hiring"))
if not doc.is_new() and not confidential and doc.status != "Closed" and not doc.custom_vendor_push_date:
    frappe.throw("Please enter the Role sharing date before saving this Job Opening.", title="Role sharing date required")
if doc.custom_vendor_push_date and doc.status == "Open":
    doc.status = shared_status
