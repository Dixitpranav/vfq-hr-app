"""Version compatibility helpers (ERPNext v15 / v16).

ERPNext v16 redesigned Budget: the `accounts` child table (Budget Account) and `fiscal_year`
were replaced by a single `account` + `budget_amount` and a `from_fiscal_year`..`to_fiscal_year`
range. The VFQ flow reads budgets through these helpers so it works on both.
"""

import frappe


def _is_v16_budget():
	return frappe.get_meta("Budget").has_field("from_fiscal_year")


def budget_header(name):
	"""company, cost_center, docstatus and fiscal_year of a Budget (fiscal_year is None when the
	v16 budget spans more than one year; use budget_covers_year for that check)."""
	if not name:
		return None
	if _is_v16_budget():
		b = frappe.db.get_value(
			"Budget", name, ["company", "cost_center", "docstatus", "from_fiscal_year", "to_fiscal_year"], as_dict=True
		)
		if not b:
			return None
		b.fiscal_year = b.from_fiscal_year if b.from_fiscal_year == b.to_fiscal_year else None
		return b
	return frappe.db.get_value("Budget", name, ["company", "cost_center", "fiscal_year", "docstatus"], as_dict=True)


def budget_accounts(name):
	"""[{account, budget_amount}] of a Budget."""
	if not name:
		return []
	if _is_v16_budget():
		b = frappe.db.get_value("Budget", name, ["account", "budget_amount"], as_dict=True)
		return [b] if b and b.account else []
	return frappe.get_all(
		"Budget Account", filters={"parent": name, "parenttype": "Budget"}, fields=["account", "budget_amount"]
	)


def _year_start(fy):
	return frappe.db.get_value("Fiscal Year", fy, "year_start_date") if fy else None


def budget_covers_year(name, fiscal_year):
	if not (name and fiscal_year):
		return True
	if not _is_v16_budget():
		return str(frappe.db.get_value("Budget", name, "fiscal_year") or fiscal_year) == str(fiscal_year)
	b = frappe.db.get_value("Budget", name, ["from_fiscal_year", "to_fiscal_year"], as_dict=True) or {}
	start, frm, to = _year_start(fiscal_year), _year_start(b.get("from_fiscal_year")), _year_start(b.get("to_fiscal_year"))
	if not (start and frm and to):
		return True
	return frm <= start <= to


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def budget_line_query(doctype, txt, searchfield, start, page_len, filters):
	"""Link query for Budget Line pickers: submitted budgets of a cost center covering a fiscal year."""
	filters = frappe._dict(filters or {})
	cond = {"docstatus": 1}
	if filters.get("cost_center"):
		cond["cost_center"] = filters.cost_center
	if filters.get("company"):
		cond["company"] = filters.company
	if txt:
		cond["name"] = ["like", f"%{txt}%"]
	title = "custom_budget_title" if frappe.get_meta("Budget").has_field("custom_budget_title") else "name"
	rows = frappe.get_all("Budget", filters=cond, fields=["name", title], order_by="name desc", limit_page_length=0)
	fy = filters.get("fiscal_year")
	rows = [r for r in rows if budget_covers_year(r.name, fy)]
	start, page_len = int(start or 0), int(page_len or 20)
	return [[r.name, r.get(title) or ""] for r in rows[start : start + page_len]]
