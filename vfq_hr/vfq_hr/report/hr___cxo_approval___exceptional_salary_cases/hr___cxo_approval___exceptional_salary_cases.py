# Copyright (c) 2026, ERPion
# License: MIT

from vfq_hr.runner import run_report_script


def execute(filters=None):
	return run_report_script(__file__, filters)
