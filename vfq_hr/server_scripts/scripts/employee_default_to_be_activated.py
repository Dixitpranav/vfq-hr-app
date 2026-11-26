# Server Script: Employee - Default To Be Activated
# Type: DocType Event | DocType: Employee | Event: Before Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

doc.status = "Inactive"
doc.custom_activation_status = "To be activated"
