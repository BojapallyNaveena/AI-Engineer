from datetime import datetime, timezone, timedelta
import re
from typing import Optional


RELATIVE_DATE_PATTERN = re.compile(
    r'(\d+)\s+(second|sec|minute|min|hour|hr|day|week|month)s?\s+ago',
    re.IGNORECASE
)

DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S GMT",
]


def parse_relative_date(date_str: str, now: Optional[datetime] = None) -> Optional[datetime]:
    """Parse relative date expressions like '2 hours ago' or '3 days ago'."""
    match = RELATIVE_DATE_PATTERN.search(date_str.strip())
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2).lower()

    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if "sec" in unit:
        delta = timedelta(seconds=amount)
    elif "min" in unit:
        delta = timedelta(minutes=amount)
    elif "hour" in unit or "hr" in unit:
        delta = timedelta(hours=amount)
    elif "day" in unit:
        delta = timedelta(days=amount)
    elif "week" in unit:
        delta = timedelta(weeks=amount)
    elif "month" in unit:
        delta = timedelta(days=amount * 30)
    else:
        return None

    return now - delta


def parse_date(date_str: Optional[str], reference_now: Optional[datetime] = None) -> Optional[str]:
    """
    Parse a date string from various formats (ISO, absolute, relative)
    and normalize to ISO-8601 UTC string (e.g. YYYY-MM-DDTHH:MM:SSZ).
    Returns None if date cannot be established.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    cleaned = date_str.strip()
    if not cleaned:
        return None

    # 1. Try relative date parsing first
    rel_dt = parse_relative_date(cleaned, reference_now)
    if rel_dt:
        return rel_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 2. Try ISO format using datetime.fromisoformat if available
    try:
        # Replace trailing 'Z' with '+00:00' for Python fromisoformat
        iso_clean = cleaned
        if iso_clean.endswith('Z'):
            iso_clean = iso_clean[:-1] + '+00:00'
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        pass

    # 3. Try common explicit date formats
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    return None


def is_within_24_hours(published_date_str: Optional[str], reference_now: Optional[datetime] = None) -> bool:
    """
    Freshness rule: check if a record's publication date is within the previous 24 hours.
    Returns False if publication date is invalid or missing.
    """
    if not published_date_str:
        return False

    parsed_iso = parse_date(published_date_str, reference_now)
    if not parsed_iso:
        return False

    try:
        pub_dt = datetime.fromisoformat(parsed_iso.replace('Z', '+00:00'))
        if reference_now is None:
            now_dt = datetime.now(timezone.utc)
        elif reference_now.tzinfo is None:
            now_dt = reference_now.replace(tzinfo=timezone.utc)
        else:
            now_dt = reference_now.astimezone(timezone.utc)

        diff = now_dt - pub_dt
        return timedelta(seconds=0) <= diff <= timedelta(hours=24)
    except Exception:
        return False
