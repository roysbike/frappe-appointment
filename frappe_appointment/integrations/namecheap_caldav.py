# Namecheap Private Email calendar is CalDAV at dav.privateemail.com.
# Apple Calendar on Mac and iPhone syncs the same account.

import base64
import re
import uuid
from datetime import datetime, timedelta
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import frappe
from frappe.utils.password import decrypt

PROPFIND_PRINCIPAL = """<?xml version="1.0" encoding="utf-8"?>
<d:propfind xmlns:d="DAV:"><d:prop><d:current-user-principal/></d:prop></d:propfind>
"""
PROPFIND_HOME = """<?xml version="1.0" encoding="utf-8"?>
<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop><c:calendar-home-set/></d:prop>
</d:propfind>
"""
PROPFIND_CALENDARS = """<?xml version="1.0" encoding="utf-8"?>
<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:prop><d:resourcetype/><c:supported-calendar-component-set/></d:prop>
</d:propfind>
"""


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
    server = (availability.caldav_server or "https://dav.privateemail.com").rstrip("/")
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
    key = f"namecheap-caldav:{availability_name}"
    cached = cache.get_value(key)
    if cached:
        return cached
    principal = _href(server + "/", username, password, PROPFIND_PRINCIPAL, "current-user-principal")
    home = _href(_absolute(server, principal), username, password, PROPFIND_HOME, "calendar-home-set")
    home_url = _absolute(server, home)
    status, payload = _request(
        home_url,
        "PROPFIND",
        username,
        password,
        PROPFIND_CALENDARS.encode(),
        {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"},
    )
    if status >= 400:
        frappe.throw(frappe._("Could not list Namecheap calendars for {0} ({1}).").format(username, status))
    calendar = _first_event_calendar(payload, home_url)
    cache.set_value(key, calendar, expires_in_sec=3600)
    return calendar


def _href(url, username, password, body, tag):
    status, payload = _request(
        url,
        "PROPFIND",
        username,
        password,
        body.encode(),
        {"Depth": "0", "Content-Type": "application/xml; charset=utf-8"},
    )
    if status >= 400:
        frappe.throw(frappe._("Namecheap CalDAV discovery failed ({0}).").format(status))
    root = __import__("xml.etree.ElementTree", fromlist=["ElementTree"]).fromstring(payload)
    node = None
    for element in root.iter():
        if element.tag.endswith("}" + tag) or element.tag == tag:
            node = element
            break
    if node is None:
        frappe.throw(frappe._("Namecheap CalDAV did not return {0}.").format(tag))
    for element in node.iter():
        if (element.tag.endswith("}href") or element.tag == "href") and element.text:
            return element.text.strip()
    frappe.throw(frappe._("Namecheap CalDAV did not return a href for {0}.").format(tag))


def _first_event_calendar(payload, home_url):
    root = __import__("xml.etree.ElementTree", fromlist=["ElementTree"]).fromstring(payload)
    for response in root.iter():
        if not (response.tag.endswith("}response") or response.tag == "response"):
            continue
        href = None
        is_calendar = False
        for element in response.iter():
            if (element.tag.endswith("}href") or element.tag == "href") and href is None and element.text:
                href = element.text.strip()
            if element.tag.endswith("}calendar") or element.tag == "calendar":
                is_calendar = True
        if href and is_calendar:
            url = _absolute(home_url, href)
            if url.rstrip("/") != home_url.rstrip("/"):
                return url if url.endswith("/") else url + "/"
    return home_url if home_url.endswith("/") else home_url + "/"


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


def _absolute(base, href):
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return urljoin(base if base.endswith("/") else base + "/", href)


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
