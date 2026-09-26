import importlib.util
import unittest
from pathlib import Path

# Load the module by path. Importing the frappe_appointment package runs
# monkey_patch, which needs a bench. These checks do not.
_spec = importlib.util.spec_from_file_location(
    "calendar_backend",
    Path(__file__).resolve().parents[1] / "integrations" / "calendar_backend.py",
)
_backend = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_backend)
should_query_google = _backend.should_query_google
format_system_time_as_utc = _backend.format_system_time_as_utc
GOOGLE_CALENDAR = _backend.GOOGLE_CALENDAR
NAMECHEAP_CALDAV = _backend.NAMECHEAP_CALDAV


class TestShouldQueryGoogle(unittest.TestCase):
    def test_caldav_never_opens_google_even_when_google_is_enabled(self):
        self.assertFalse(should_query_google(NAMECHEAP_CALDAV, True))

    def test_caldav_stays_off_when_google_is_disabled(self):
        self.assertFalse(should_query_google(NAMECHEAP_CALDAV, False))

    def test_google_source_queries_google_only_when_enabled(self):
        self.assertTrue(should_query_google(GOOGLE_CALENDAR, True))
        self.assertFalse(should_query_google(GOOGLE_CALENDAR, False))

    def test_empty_source_defaults_to_google(self):
        self.assertTrue(should_query_google(None, True))
        self.assertFalse(should_query_google("", False))


class TestCaldavTime(unittest.TestCase):
    def test_dubai_14_00_is_10_00_utc(self):
        self.assertEqual(format_system_time_as_utc("2026-09-28 14:00:00", "Asia/Dubai"), "20260928T100000Z")

    def test_dubai_15_00_end_is_11_00_utc(self):
        self.assertEqual(format_system_time_as_utc("2026-09-28 15:00:00", "Asia/Dubai"), "20260928T110000Z")


_phone_spec = importlib.util.spec_from_file_location(
    "booking_contact",
    Path(__file__).resolve().parents[1] / "helpers" / "booking_contact.py",
)
_phone = importlib.util.module_from_spec(_phone_spec)
_phone_spec.loader.exec_module(_phone)


class TestBookingPhone(unittest.TestCase):
    def test_blank_phone_is_omitted(self):
        self.assertEqual(_phone.normalize_booking_phone("  "), "")
        self.assertEqual(_phone.description_with_phone("Meet link", ""), "Meet link")

    def test_uae_number_is_stored_on_the_description(self):
        phone = _phone.normalize_booking_phone("+971 50 123 4567")
        self.assertEqual(phone, "+971 50 123 4567")
        self.assertEqual(_phone.description_with_phone("", phone), "Phone: +971 50 123 4567")

    def test_dubai_selection_is_labeled_dubai_not_ist(self):
        text = _phone.format_appointment_when("2026-09-29 14:00:00", "Asia/Dubai", "Asia/Dubai")
        self.assertEqual(text, "Tuesday, 29 September 2026 at 02:00 pm (Dubai)")

    def test_kolkata_selection_shifts_the_clock(self):
        text = _phone.format_appointment_when("2026-09-29 14:00:00", "Asia/Dubai", "Asia/Kolkata")
        self.assertEqual(text, "Tuesday, 29 September 2026 at 03:30 pm (Kolkata)")

    def test_unknown_timezone_uses_the_site_zone(self):
        text = _phone.format_appointment_when("2026-09-29 14:00:00", "Asia/Dubai", "Not/AZone")
        self.assertIn("(Dubai)", text)

    def test_short_or_text_phone_is_rejected(self):
        with self.assertRaises(ValueError):
            _phone.normalize_booking_phone("123")
        with self.assertRaises(ValueError):
            _phone.normalize_booking_phone("call me")


_slot_spec = importlib.util.spec_from_file_location(
    "slot_blocks",
    Path(__file__).resolve().parents[1] / "helpers" / "slot_blocks.py",
)
_slots = importlib.util.module_from_spec(_slot_spec)
_slot_spec.loader.exec_module(_slots)


class TestBookedSlot(unittest.TestCase):
    def test_booked_meeting_is_added_and_sorted_before_later_busy_time(self):
        calendar = [{"starts_on": "2026-09-29 15:00:00", "ends_on": "2026-09-29 15:15:00"}]
        booked = [{"starts_on": "2026-09-29 14:00:00", "ends_on": "2026-09-29 14:15:00"}]
        merged = _slots.with_booked_intervals(calendar, booked)
        self.assertEqual(merged[0]["starts_on"], "2026-09-29 14:00:00")
        self.assertEqual(merged[1]["starts_on"], "2026-09-29 15:00:00")

    def test_empty_or_reversed_booking_is_ignored(self):
        self.assertEqual(_slots.with_booked_intervals([], [{"starts_on": "b", "ends_on": "a"}]), [])


if __name__ == "__main__":
    unittest.main()
