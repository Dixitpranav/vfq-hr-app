# Server Script: Bulk Create Performance Reviews
# Type: API | API method: bulk_create_performance_reviews
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Bulk create Mid-Year / Annual Performance Reviews (HR only).
# action = "preview" returns every employee matching the vendor / project filters with eligibility and reasons.
# action = "create" re-checks eligibility on the server and creates Draft reviews for the chosen employees.
def run_script():
    fd = frappe.form_dict
    user = frappe.session.user
    roles = frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")
    if user != "Administrator" and not ("HR User" in roles or "HR Manager" in roles):
        frappe.throw("Only HR can create reviews in bulk.", title="Not Allowed")

    review_type = fd.review_type
    if review_type not in ("Mid-Year Review", "Annual Performance Review"):
        frappe.throw("Unknown review type.")
    is_mid = review_type == "Mid-Year Review"
    period = fd.review_period or ""
    year = str(fd.review_year or "").strip()
    if not year:
        frappe.throw("Please choose the Review Year.")
    if is_mid and not period:
        frappe.throw("Please choose the Review Period (H1 or H2).")

    vendors = json.loads(fd.vendors or "[]")
    projects = json.loads(fd.projects or "[]")
    if not vendors and not projects:
        frappe.throw("Select at least one Vendor or Project to choose the employees.")

    filters = {"status": "Active"}
    if vendors:
        filters["custom_vendor"] = ["in", vendors]
    if projects:
        filters["custom_project"] = ["in", projects]
    emps = frappe.get_all("Employee", filters=filters, fields=["name", "employee_name", "custom_vendor", "custom_project", "custom_project_name", "date_of_joining", "department", "designation", "reports_to", "custom_confirmation_status"], order_by="employee_name asc")

    today = frappe.utils.getdate(frappe.utils.nowdate())
    label = ("Mid-Year Review " + period + " " + year) if is_mid else ("Annual Performance Review " + year)
    rows = []
    for e in emps:
        reasons = []
        if not e.date_of_joining:
            reasons.append("No Date of Joining on the employee record")
        else:
            six = frappe.utils.getdate(frappe.utils.add_months(e.date_of_joining, 6))
            if six > today:
                reasons.append("Less than 6 months since joining (eligible from " + frappe.utils.formatdate(six) + ")")
        if not frappe.db.exists("Probation Review", {"employee": e.name, "docstatus": 1}):
            reasons.append("No submitted Probation Review")
        open_pr = frappe.db.get_value("Probation Review", {"employee": e.name, "docstatus": 0}, "name")
        if open_pr:
            reasons.append("Probation Review " + open_pr + " is not submitted yet")
        if frappe.db.exists("Probation Extension", {"employee": e.name, "workflow_state": "Pending HR Approval"}):
            reasons.append("Probation extension pending HR approval")
        open_exit = frappe.get_all("Employee Exit", filters={"employee": e.name, "workflow_state": ["!=", "Rejected"], "docstatus": ["!=", 2]}, fields=["name", "workflow_state"], limit_page_length=1)
        if open_exit:
            reasons.append("Has a resignation / exit record " + open_exit[0].name + " (" + (open_exit[0].workflow_state or "Draft") + ")")
        if e.custom_confirmation_status in ("Probation", "Extended", "Terminated"):
            reasons.append("Confirmation status is " + e.custom_confirmation_status)
        if not is_mid and not frappe.db.exists("Mid-Year Review", {"employee": e.name, "review_year": year, "workflow_state": "Completed"}):
            reasons.append("No Completed Mid-Year Review for " + year)
        if is_mid:
            dup = frappe.db.get_value("Mid-Year Review", {"employee": e.name, "review_period": period, "review_year": year, "docstatus": ["!=", 2]}, "name")
        else:
            dup = frappe.db.get_value("Annual Performance Review", {"employee": e.name, "review_year": frappe.utils.cint(year), "docstatus": ["!=", 2]}, "name")
        if dup:
            reasons.append(label + " already exists (" + dup + ")")
        rows.append({"employee": e.name, "employee_name": e.employee_name, "vendor": e.custom_vendor, "project": e.custom_project_name or e.custom_project, "date_of_joining": e.date_of_joining, "eligible": 0 if reasons else 1, "reasons": reasons, "e": e})

    if fd.action != "create":
        out = []
        for r in rows:
            out.append({"employee": r["employee"], "employee_name": r["employee_name"], "vendor": r["vendor"], "project": r["project"], "date_of_joining": r["date_of_joining"], "eligible": r["eligible"], "reasons": r["reasons"]})
        frappe.response["message"] = {"rows": out}
        return

    chosen = json.loads(fd.employees or "[]")
    created = []
    skipped = []
    for r in rows:
        if r["employee"] not in chosen:
            continue
        if not r["eligible"]:
            skipped.append({"employee": r["employee"], "reason": "; ".join(r["reasons"])})
            continue
        e = r["e"]
        data = {"doctype": review_type, "employee": e.name, "employee_name": e.employee_name, "department": e.department, "designation": e.designation, "reporting_manager": e.reports_to}
        if is_mid:
            data["review_period"] = period
            data["review_year"] = year
        else:
            data["review_year"] = frappe.utils.cint(year)
        try:
            d = frappe.get_doc(data)
            d.insert(ignore_mandatory=True)
            created.append({"employee": e.name, "employee_name": e.employee_name, "name": d.name})
        except Exception as ex:
            skipped.append({"employee": e.name, "reason": str(ex)})
    frappe.response["message"] = {"created": created, "skipped": skipped}

run_script()
