import unittest

from frappe_appointment.integrations.calendar_backend import (
    GOOGLE_CALENDAR,
    NAMECHEAP_CALDAV,
    should_query_google,
)


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


if __name__ == "__main__":
    unittest.main()
