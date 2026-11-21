"""Deterministic date arithmetic; no legal time limits are encoded here."""
from datetime import date
from dateutil.relativedelta import relativedelta


def compute_seniority(start_date: str, end_date: str) -> dict:
    """Compute calendar years, months, and days between ISO dates, with steps."""
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    delta = relativedelta(end, start)
    after_years = start + relativedelta(years=delta.years)
    return {"years": delta.years, "months": delta.months, "days": delta.days,
            "calculation_steps": [f"Start at {start.isoformat()}.",
                                  f"Add {delta.years} calendar year(s): {after_years.isoformat()}.",
                                  f"Add {delta.months} calendar month(s), then {delta.days} day(s), to reach {end.isoformat()}."]}

