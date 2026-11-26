# VFQ HR build report

Generated from `testingappversion15.frappe.cloud` (Frappe 15.124 / ERPNext 15.124 / HRMS 15.64) on 25 Nov 2026,
checked against Frappe v16 / ERPNext v16 / HRMS v16 source (version-16 branches).

## Included

| Item | Count | How |
|---|---|---|
| Custom DocTypes | 27 | App DocTypes, module VFQ HR |
| Server Scripts (business rules) | 150 | Verbatim; 146 byte-identical, 4 with band lines removed. Compiled and run exactly like Server Scripts (RestrictedPython + Frappe policy) from app hooks |
| Doc event hooks | 16 doctypes | `doc_events` → `vfq_hr.runner.run_doc_event` (same event mapping and order as Frappe's server-script map) |
| Permission query rules | 17 doctypes | `permission_query_conditions` |
| API methods | 11 | Same short names via `override_whitelisted_methods` (forms keep calling e.g. `activate_employee`) |
| Scheduled jobs | 3 | 2 daily, 1 monthly |
| Client Scripts | 39 | `doctype_js` / `doctype_list_js`, same order as on the site |
| Reports | 22 | Standard Script Reports, module VFQ HR |
| Workspaces | 7 | HR, Masters, Reports, Self Service Portal, Employee Self Service, Manager Self Service, HR Self Service Console (app-owned) |
| Custom Fields | 324 | Site-made fields on flow doctypes only |
| Property Setters | 316 | Site-made, flow doctypes only |
| Role permissions | 480 rows / 61 doctypes | Flow doctypes and the masters they link to |
| Roles | 18 | CAO, CEO / Final Approver, CFO, CHRO, CSCO, CTO, Employee Self Service, Functional Head, HOD, HR Ops, HR Ops - VFQ Email, Head of OD & Total Rewards, Job Opening Vendor, Line Manager, Recruitment Specialist, Reporting Manager, Vendor Manager, Workforce Plan Creator |
| Workflows | 11 | With 27 states and 25 actions |
| Notifications | 86 | Enabled/disabled exactly as on the site (4 enabled) |
| Print formats / Web forms | 4 / 2 | |
| Dashboard / charts / number cards | 1 / 5 / 5 | Hiring Flow Dashboard |
| Seed masters (insert-only) | | Function tree, Exit Reason, KRA Category, Employment Type, Job Applicant Source, Designation, Leave Type, Leave Policy, Leave Policy Mapping, Interview Type/Round, Job Opening Template |

## Excluded by decision

- Salary bands / sub-bands: HR Band, HR Sub Band, HR Salary Band Table, JR Band Variance Log, 17 band fields,
  the "Reason for Variance" field, the band validation script, the Band Variance report, band columns in 7 reports
  (salary range columns relabelled "Salary Range Low/Mid/Max"). Performance-review bands are kept.
- AI Governance (hr_ai_agents app, AI roles, AI users, AI Governance workspace).
- HR Analytics app, Insights dashboards.
- Salon / POS / sales / stock customisations and dashboards from the demo.
- Disabled reports (HR Lifecycle, Replacement Cost Impact, folded into Traceability and JR Role Detail) and a personal test report.

## Adjusted for portability

- Notification `sender` cleared: the target site uses its own default outgoing Email Account.
- Interview Round seed data: interviewer users removed (they are site users).
- Five custom fields that sat after a removed band field are re-anchored to the same position.
- Saved field orders no longer list band fields.

## Navigation and upgrade safety

- v16: other apps' workspaces are restricted to System Manager through **Custom Workspace** (the v16 site-level
  override layer that app updates do not overwrite); other apps' desktop icons are restricted to System Manager.
- v15: the same pages as the source site are hidden / restricted to System Manager.
- Both are re-applied after every `bench migrate`, together with fixtures, so ERPNext / HRMS updates cannot change the flow.
- VFQ HR appears on the apps screen (`add_to_apps_screen`).

## Things to check on the first v16 install

1. HRMS v16 renamed two layout breaks (Job Applicant `section_break_16`, Job Opening `column_break_20`): one custom
   field on each form may sit at a different position. Adjust with Customize Form if needed.
2. v16.50 navigation: confirm the VFQ HR app tile, its sidebar, and that HR roles no longer see Frappe HR / ERPNext menus.
3. Run `vfq_hr.tools.parity.run` and `vfq_hr.tools.parity.smoke_reports`.

## Site data not carried by the app (set up on the target site)

Users, user permissions, employees, departments (`vfq_hr.install.create_departments`), holiday lists, leave allocations,
companies, cost centres, budgets, email accounts.
