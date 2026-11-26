# Server Script: Annual Performance Review - Compute Scores and Band
# Type: DocType Event | DocType: Annual Performance Review | Event: Before Save
# Runs with the same variables as a Frappe Server Script (see vfq_hr/runner.py).

# Same scoring as the form, run on the server so API / import entries get scores and a band too.
total_weighted = 0
total_weight = 0
for kra_row in (doc.get("kra_evaluation") or []):
    total_weighted += frappe.utils.flt(kra_row.weightage) * frappe.utils.flt(kra_row.rating)
    total_weight += frappe.utils.flt(kra_row.weightage)
kra_value = (total_weighted / total_weight) if total_weight > 0 else 0
competencies = [frappe.utils.flt(doc.technical_skills), frappe.utils.flt(doc.communication), frappe.utils.flt(doc.teamwork), frappe.utils.flt(doc.leadership), frappe.utils.flt(doc.problem_solving), frappe.utils.flt(doc.innovation)]
competency_value = sum(competencies) / len(competencies)
final_value = (kra_value * 0.7) + (competency_value * 0.3)
doc.kra_score = round(kra_value, 2)
doc.competency_score = round(competency_value, 2)
doc.final_rating = round(final_value, 2)
if final_value > 4.5:
    doc.performance_band = "Outstanding"
elif final_value > 4.0:
    doc.performance_band = "Exceeds Expectations"
elif final_value > 3.0:
    doc.performance_band = "Meets Expectations"
elif final_value > 2.0:
    doc.performance_band = "Needs Improvement"
else:
    doc.performance_band = "Unsatisfactory"
