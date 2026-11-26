# Auto-generated: scheduled jobs backed by the site's Scheduler Event scripts.
from vfq_hr.runner import run_scheduled


def job_job_applicant_refresh_ageing_daily():
	run_scheduled('Job Applicant - Refresh Ageing Daily')


def job_job_opening_close_expired_shared_openings():
	run_scheduled('Job Opening - Close Expired Shared Openings')


def job_post_workforce_plan_payroll_accrual_periodic():
	run_scheduled('Post Workforce Plan Payroll Accrual (Periodic)')
