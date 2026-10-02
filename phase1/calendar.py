from datetime import date

import holidays

from .models import Occasion


def upcoming_indian_occasions(
    today: date,
    minimum_lead_days: int = 20,
    horizon_days: int = 120,
) -> list[Occasion]:
    """Return occasions far enough ahead to support content planning."""
    calendar = holidays.country_holidays("IN", years=range(today.year, today.year + 2))
    occasions = []
    for occasion_date, name in sorted(calendar.items()):
        days_until = (occasion_date - today).days
        if minimum_lead_days <= days_until <= horizon_days:
            occasions.append(
                Occasion(
                    name=name,
                    date=occasion_date,
                    days_until=days_until,
                    relevance="Potential occasion for culturally relevant fashion content.",
                )
            )
    return occasions