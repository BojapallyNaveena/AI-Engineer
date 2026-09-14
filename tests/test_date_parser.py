import unittest
from datetime import datetime, timezone, timedelta
from src.parsers.date_parser import parse_date, is_within_24_hours, parse_relative_date


class TestDateParser(unittest.TestCase):
    def test_parse_iso_dates(self):
        self.assertEqual(parse_date("2024-01-15T10:30:00Z"), "2024-01-15T10:30:00Z")
        self.assertEqual(parse_date("2024-01-15T10:30:00+00:00"), "2024-01-15T10:30:00Z")

    def test_parse_absolute_dates(self):
        self.assertEqual(parse_date("2024-01-15"), "2024-01-15T00:00:00Z")
        self.assertEqual(parse_date("15 Jan 2024"), "2024-01-15T00:00:00Z")
        self.assertEqual(parse_date("January 15, 2024"), "2024-01-15T00:00:00Z")

    def test_parse_relative_dates(self):
        ref_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # 2 hours ago from 12:00 -> 10:00
        res = parse_date("2 hours ago", reference_now=ref_now)
        self.assertEqual(res, "2024-01-15T10:00:00Z")
        
        # 1 day ago -> 2024-01-14T12:00:00Z
        res_day = parse_date("1 day ago", reference_now=ref_now)
        self.assertEqual(res_day, "2024-01-14T12:00:00Z")

    def test_invalid_date(self):
        self.assertIsNone(parse_date("not a date string"))
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date(""))

    def test_is_within_24_hours(self):
        ref_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        # 5 hours ago -> fresh
        pub_fresh = "2024-01-15T07:00:00Z"
        self.assertTrue(is_within_24_hours(pub_fresh, reference_now=ref_now))
        
        # 25 hours ago -> not fresh
        pub_old = "2024-01-14T10:00:00Z"
        self.assertFalse(is_within_24_hours(pub_old, reference_now=ref_now))
        
        # Invalid date -> not fresh
        self.assertFalse(is_within_24_hours(None, reference_now=ref_now))


if __name__ == "__main__":
    unittest.main()
