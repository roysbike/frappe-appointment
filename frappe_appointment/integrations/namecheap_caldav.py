# cPanel CalDAV for a mailbox. Namecheap shows it under Secure SSL/TLS URLs:
# https://<domain>:2080/calendars/<mailbox>/calendar
# Apple Calendar on Mac and iPhone syncs that same collection.

import base64
import re
import uuid
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

import frappe
from frappe.utils.password import decrypt

def busy_events(availability_name, day):
    """Busy blocks shaped like Google events so the existing slot filter can use them."""
    availability = frappe.get_doc("User Appointment Availability", availability_name)
    username, password, server = _credentials(availability)
    calendar_url = _calendar_url(availability_name, username, password, server)
    start, end = _day_bounds(day)
    body = f"""<?xml version="1.0" encoding="utf-8"?>
<c:free-busy-query xmlns:c="urn:ietf:params:xml:ns:caldav">
  <c:time-range start="{_stamp(start)}" end="{_stamp(end)}"/>
</c:free-busy-query>
""".encode()
    status, payload = _request(
        calendar_url,
        "REPORT",
        username,
        password,
        body,
        {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
    )
    if status >= 400:
        frappe.throw(
            frappe._("Namecheap calendar refused the busy check for {0} ({1}).").format(username, status)
        )
    events = []
    for raw_start, raw_end in _freebusy_ranges(payload):
        events.append(
            {
                "creator": {"email": availability.user},
                "start": {"dateTime": raw_start, "timeZone": "UTC"},
                "end": {"dateTime": raw_end, "timeZone": "UTC"},
            }
        )
    return events


def check_connection(availability):
    """PROPFIND the cPanel calendar. Used when the availability is saved."""
    username = availability.caldav_username
    password = availability.get_password("caldav_app_password")
    server = (availability.caldav_server or "").strip().rstrip("/")
    frappe.cache().delete_value(f"namecheap-caldav:{availability.name}:{server}")
    calendar_url = _calendar_url(availability.name, username, password, server)
    status, _payload = _request(
        calendar_url,
        "PROPFIND",
        username,
        password,
        b"""<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:"><D:prop><D:displayname/></D:prop></D:propfind>""",
        {"Depth": "0", "Content-Type": "application/xml; charset=utf-8"},
    )
    if status in (200, 207):
        return calendar_url
    if status in (401, 403):
        frappe.throw(
            frappe._("CalDAV login failed for {0} at {1} ({2}).").format(username, calendar_url, status)
        )
    frappe.throw(
        frappe._("CalDAV calendar was not found for {0} at {1} ({2}).").format(username, calendar_url, status)
    )


def create_event(availability_name, uid, summary, starts_on, ends_on, description=""):
    availability = frappe.get_doc("User Appointment Availability", availability_name)
    username, password, server = _credentials(availability)
    calendar_url = _calendar_url(availability_name, username, password, server)
    href = calendar_url.rstrip("/") + "/" + uid + ".ics"
    status, _payload = _request(
        href,
        "PUT",
        username,
        password,
        _vevent(uid, summary, starts_on, ends_on, description).encode(),
        {"Content-Type": "text/calendar; charset=utf-8"},
    )
    if status not in (200, 201, 204):
        frappe.throw(
            frappe._("Namecheap calendar did not save the appointment for {0} ({1}).").format(username, status)
        )
    return href


def _credentials(availability):
    if not availability.caldav_username:
        frappe.throw(frappe._("Set the Namecheap mailbox on the availability."))
    password = _read_password(availability.name)
    server = (availability.caldav_server or "").strip().rstrip("/")
    return availability.caldav_username, password, server


def _read_password(name):
    # Public booking runs as Guest. The mailbox password is not returned to the guest.
    encrypted = frappe.db.sql(
        "select `password` from `__Auth` where doctype=%s and name=%s and fieldname=%s",
        ("User Appointment Availability", name, "caldav_app_password"),
    )
    if not encrypted:
        frappe.throw(frappe._("Namecheap application password is missing."))
    return decrypt(encrypted[0][0])


def _calendar_url(availability_name, username, password, server):
    cache = frappe.cache()
    key = f"namecheap-caldav:{availability_name}:{server}"
    cached = cache.get_value(key)
    if cached:
        return cached
    # cPanel default calendar. Example: https://mybooks.ae:2080/calendars/kgo@mybooks.ae/calendar
    if "/calendars/" in server:
        calendar = server if server.endswith("/") else server + "/"
    else:
        if "@" not in username:
            frappe.throw(frappe._("Mailbox must be a full address, for example kgo@mybooks.ae."))
        host = server or f"https://{username.split('@', 1)[1]}:2080"
        calendar = f"{host}/calendars/{username}/calendar/"
    cache.set_value(key, calendar, expires_in_sec=3600)
    return calendar


def _request(url, method, username, password, body=None, headers=None):
    request = Request(url, data=body, method=method)
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    request.add_header("Authorization", f"Basic {token}")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except Exception as err:
        if hasattr(err, "code"):
            payload = err.read() if hasattr(err, "read") else b""
            return err.code, payload
        frappe.throw(frappe._("Could not reach Namecheap calendar: {0}").format(err))


def _freebusy_ranges(payload):
    text = payload.decode("utf-8", errors="replace")
    ranges = []
    for match in re.finditer(r"FREEBUSY(?:;FBTYPE=([^:]+))?:([0-9TZ]+)/([0-9TZ]+)", text):
        kind = (match.group(1) or "BUSY").upper()
        if kind not in ("BUSY", "BUSY-UNAVAILABLE", "BUSY-TENTATIVE"):
            continue
        ranges.append((_iso(match.group(2)), _iso(match.group(3))))
    return ranges


def _iso(stamp):
    parsed = datetime.strptime(stamp.replace("Z", ""), "%Y%m%dT%H%M%S")
    return parsed.strftime("%Y-%m-%dT%H:%M:%S")


def _stamp(moment):
    return moment.strftime("%Y%m%dT%H%M%SZ")


def _day_bounds(day):
    if isinstance(day, str):
        day = datetime.strptime(day[:10], "%Y-%m-%d")
    start = datetime(day.year, day.month, day.day)
    return start, start + timedelta(days=1)


def _vevent(uid, summary, starts_on, ends_on, description):
    def _fmt(value):
        if isinstance(value, str):
            value = datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
        return value.strftime("%Y%m%dT%H%M%SZ")

    safe_summary = (summary or "Appointment").replace("\n", " ")
    safe_description = (description or "").replace("\n", "\\n")
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//mybooks//frappe-appointment//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{_stamp(datetime.utcnow())}\r\n"
        f"DTSTART:{_fmt(starts_on)}\r\n"
        f"DTEND:{_fmt(ends_on)}\r\n"
        f"SUMMARY:{safe_summary}\r\n"
        f"DESCRIPTION:{safe_description}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def new_uid():
    return uuid.uuid4().hex
