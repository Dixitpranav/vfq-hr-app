# Server Script: Job Opening - Lock After Shared With Vendor
# Type: DocType Event | DocType: Job Opening | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

before = doc.get_doc_before_save()
if before and before.status == "Open & To be shared with vendor" and doc.status != "Closed":
    frappe.throw("This Job Opening has been shared with the vendor and can no longer be changed.", title="Locked")
