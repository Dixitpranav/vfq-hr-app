# Server Script: Workforce Plan - Duplicate Position Check
# Type: DocType Event | DocType: Workforce Plan | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

seen = {}
warnings = []
for i, row in enumerate(doc.positions):
    fn = row.get("function") or ""
    dept = row.get("sub_function") or ""
    pos = row.get("position") or ""
    hm = row.get("hiring_manager") or ""
    key = fn + "||" + dept + "||" + pos + "||" + hm
    if key in seen:
        prev = seen[key] + 1
        curr = i + 1
        warnings.append(
            "Row " + str(curr) + " has the same Function, Department, Position and Hiring Manager as Row " + str(prev) + "."
        )
    seen[key] = i

if warnings:
    frappe.msgprint(
        "Possible duplicate position(s) detected (same Function, Department, Position and Hiring Manager) -- please double check:<br>" + "<br>".join(warnings),
        title="Duplicate Position Warning",
        indicator="orange"
    )
