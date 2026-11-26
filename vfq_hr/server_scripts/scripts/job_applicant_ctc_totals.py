# Server Script: Job Applicant - CTC Totals
# Type: DocType Event | DocType: Job Applicant | Event: Before Validate
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Gross = Basic + Allowance, CTC = Gross + Benefits (all yearly USD). Monthly figures are yearly / 12.
flt = frappe.utils.flt
doc.custom_ctc_gross = flt(doc.custom_ctc_basic) + flt(doc.custom_ctc_allowance)
doc.custom_ctc_total = doc.custom_ctc_gross + flt(doc.custom_ctc_benefits)
doc.custom_ctc_basic_monthly = flt(doc.custom_ctc_basic) / 12.0
doc.custom_ctc_allowance_monthly = flt(doc.custom_ctc_allowance) / 12.0
doc.custom_ctc_gross_monthly = doc.custom_ctc_gross / 12.0
doc.custom_ctc_benefits_monthly = flt(doc.custom_ctc_benefits) / 12.0
doc.custom_ctc_total_monthly = doc.custom_ctc_total / 12.0
