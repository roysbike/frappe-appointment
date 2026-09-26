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


if __name__ == "__main__":
    unittest.main()
