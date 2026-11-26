# Server Script: Workforce Plan - Generate Role Codes
# Type: DocType Event | DocType: Workforce Plan | Event: After Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

creation_str = str(doc.creation)
year = creation_str[0:4]
month_num = creation_str[5:7]
month_names = {"01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY", "06": "JUN", "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC"}
month_abbr = month_names.get(month_num, "XXX")
prefix = "WP-ROLE-" + month_abbr + "-" + year + "-"

needs_code = [row for row in doc.positions if not row.role_code]
if needs_code:
    existing = frappe.db.sql(
        "SELECT role_code FROM `tabWorkforce Plan Position` WHERE role_code LIKE %s AND role_code != ''",
        (prefix + "%",)
    )
    used_nums = set()
    for rec in existing:
        code = rec[0]
        try:
            num = int(code.replace(prefix, ""))
            used_nums.add(num)
        except Exception:
            pass

    counter = 1
    for row in needs_code:
        while counter in used_nums:
            counter = counter + 1
        row.role_code = prefix + str(counter).zfill(4)
        used_nums.add(counter)
        frappe.db.set_value("Workforce Plan Position", row.name, "role_code", row.role_code)
        counter = counter + 1
