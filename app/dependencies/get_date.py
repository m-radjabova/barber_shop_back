from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

def get_date_range(range_name: str):
    now = datetime.now(timezone.utc)
    r = (range_name or "week").lower()

    if r == "week":
        start = now - timedelta(days=7)
    elif r == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif r == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise HTTPException(status_code=400, detail="Invalid range: week/month/year")

    return start, now
