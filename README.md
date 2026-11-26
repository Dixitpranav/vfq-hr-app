# VFQ HR

The VFQ HR process on Frappe HR: Workforce Plan → Job Requisition → Job Opening → Job Applicant → CXO Hiring Approval → Employee activation (HR Ops) → Probation → Mid-Year / Annual reviews → Employee Exit, plus leave approvals, self-service scopes, reports and dashboards.

Onboarding includes HR Ops activation, a mandatory Official Email (VFQ) and the Conflict of Interest (COI) form by email.

Install it after ERPNext and Frappe HR. It works on **v16 (primary, branch `version-16`)** and v15.

## Install

```bash
bench get-app https://github.com/Dixitpranav/vfq-hr-app.git --branch version-16
bench --site <site> install-app vfq_hr
bench --site <site> migrate
```

Then create the department structure for the company and check parity:

```bash
bench --site <site> execute vfq_hr.install.create_departments --kwargs '{"company": "<Company Name>"}'
bench --site <site> execute vfq_hr.tools.parity.run
bench --site <site> execute vfq_hr.tools.parity.smoke_reports
```

`server_script_enabled` is **not** required: the business logic ships in the app.

## What is inside

| Part | Where |
|---|---|
| Custom DocTypes (Workforce Plan, CXO Hiring Approval, Probation Review, Mid-Year Review, Annual Performance Review, Employee Exit, Function, …) | `vfq_hr/vfq_hr/doctype/` |
| Business rules (the site's Server Scripts, verbatim) | `vfq_hr/server_scripts/scripts/` run by `vfq_hr/runner.py` through `hooks.py` |
| Form and list behaviour (the site's Client Scripts) | `vfq_hr/public/js/client_scripts/` via `doctype_js` / `doctype_list_js` |
| Reports (standard Script Reports) | `vfq_hr/vfq_hr/report/` |
| Fields, form settings, roles, permissions, workflows, notifications, print formats, web forms, dashboards, workspaces | `vfq_hr/fixtures/` (re-applied on every migrate) |
| Masters seeded on install (insert-only) | `vfq_hr/setup/seed_data/` |
| Sidebar visibility (hidden modules) | `vfq_hr/install.py`, re-applied after every migrate |
| Parity check | `vfq_hr/tools/parity.py` |

## Upgrade safety

- No ERPNext / Frappe HR code is overridden or patched.
- Fixtures and sidebar visibility are re-applied on every `bench migrate`, so an upgrade cannot drift the flow.
- Seed data is insert-only: changes made on the site are never overwritten.
- Before any upgrade: run `parity.run` and `parity.smoke_reports` on a staging copy.

## Maintaining fixtures

Fixture files are numbered (`01_role.json` … `15_workspace.json`) so they import in dependency order.
If you use `bench export-fixtures`, rename the exported files to the same numbered names.

Not included by design: AI Governance (separate app later), salary bands / sub-bands, Insights dashboards, the HR Analytics app.
