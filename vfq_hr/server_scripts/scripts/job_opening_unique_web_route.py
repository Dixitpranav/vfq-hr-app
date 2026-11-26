# Server Script: Job Opening - Unique Web Route
# Type: DocType Event | DocType: Job Opening | Event: Before Insert
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Job titles can repeat (e.g. two "Android Developer" openings). The web route must be unique,
# so give each new opening its own (hidden) route instead of numbering the visible title.
if not doc.route:
    parts = []
    for raw in [doc.company or "company", doc.job_title or "job-opening", doc.get("custom_role_code") or ""]:
        s = ""
        for ch in str(raw).strip().lower():
            s = s + (ch if ch.isalnum() else "-")
        while "--" in s:
            s = s.replace("--", "-")
        parts.append(s.strip("-"))
    base = "jobs/" + parts[0] + "/" + parts[1]
    if parts[2]:
        base = base + "-" + parts[2]
    doc.route = base
    n = 1
    while frappe.db.exists("Job Opening", {"route": doc.route}):
        n = n + 1
        doc.route = base + "-" + str(n)
