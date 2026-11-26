# Server Script: DocShare - No Self Access to User Record
# Type: DocType Event | DocType: DocShare | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Frappe shares every desk user's own User record with them (read + write + share).
# Only HR / System Managers may open or change User records, so that self-share is emptied for everyone else.
def run_script(doc):
    if doc.share_doctype != "User" or not doc.user or doc.user != doc.share_name:
        return
    allowed = ["System Manager", "HR Manager", "HR User", "Administrator"]
    if doc.user == "Administrator" or frappe.db.exists("Has Role", {"parent": doc.user, "parenttype": "User", "role": ["in", allowed]}):
        return
    doc.read = 0
    doc.write = 0
    doc.share = 0
    doc.submit = 0

run_script(doc)
