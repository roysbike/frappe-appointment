import re
from datetime import datetime
from zoneinfo import ZoneInfo

_PHONE = re.compile(r"^\+?[\d\s()-]+$")


def normalize_booking_phone(value) -> str:
    """Return a phone number safe to store, or an empty string when none was given."""
    phone = str(value or "").strip()
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if not _PHONE.fullmatch(phone) or not 7 <= len(digits) <= 15:
        raise ValueError("Enter a valid phone number")
    return phone


def normalize_guest_timezone(value, fallback: str) -> str:
    """IANA name chosen in the browser, or the site timezone when it is not usable."""
    name = str(value or "").strip()
    if name:
        try:
            ZoneInfo(name)
            return name
        except Exception:
            pass
    return fallback


def format_appointment_when(starts_on, system_timezone: str, guest_timezone: str = None) -> str:
    """Clock time in the timezone the guest selected, for example 02:00 pm (Dubai)."""
    if isinstance(starts_on, datetime):
        moment = starts_on.replace(tzinfo=None)
    else:
        moment = datetime.strptime(str(starts_on)[:19], "%Y-%m-%d %H:%M:%S")
    zone_name = normalize_guest_timezone(guest_timezone, system_timezone)
    local = moment.replace(tzinfo=ZoneInfo(system_timezone)).astimezone(ZoneInfo(zone_name))
    city = zone_name.split("/")[-1].replace("_", " ")
    clock = local.strftime("%I:%M %p").lower()
    return f"{local.strftime('%A, %d %B %Y')} at {clock} ({city})"


def description_with_phone(description, phone: str) -> str:
    if not phone:
        return description or ""
    line = f"Phone: {phone}"
    description = (description or "").strip()
    if not description:
        return line
    if line in description:
        return description
    return f"{description}\n{line}"
