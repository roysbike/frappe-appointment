"""Choose Google Calendar or Namecheap CalDAV without loading either document."""

from datetime import datetime
from zoneinfo import ZoneInfo

NAMECHEAP_CALDAV = "Namecheap CalDAV"
GOOGLE_CALENDAR = "Google Calendar"


def format_system_time_as_utc(value, system_timezone):
    """ERPNext stores the slot in the site timezone. CalDAV Z means UTC."""
    if isinstance(value, str):
        value = datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo(system_timezone))
    return value.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")


def should_query_google(calendar_source, google_enabled):
    """Guest booking must not open the Google Calendar doctype when this is false."""
    if (calendar_source or GOOGLE_CALENDAR) == NAMECHEAP_CALDAV:
        return False
    return bool(google_enabled)


def google_calendar_enabled():
    """Appointment Settings check. Missing column means the old default: Google stays on."""
    import frappe
    from frappe.utils import cint

    try:
        value = frappe.db.get_single_value("Appointment Settings", "enable_google_calendar")
    except Exception:
        return True
    if value is None:
        return True
    return bool(cint(value))
