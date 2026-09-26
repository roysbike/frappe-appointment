import re

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
