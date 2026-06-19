#!/usr/bin/env python3
"""
test_detector.py
Unit tests for the automated UX bug detector (detector.py).
"""

import unittest
from detector import analyze_session

class TestUXDetector(unittest.TestCase):

    def test_healthy_session(self):
        """Should not flag healthy sessions."""
        session = {
            "session_id": "test-healthy",
            "persona": "debtor",
            "duration_s": 30,
            "events": [
                {"t": 0, "type": "$pageview", "pathname": "/pay/INV-123"},
                {"t": 5, "type": "$autocapture", "event": "click", "element": "button", "text": "Pay now"},
                {"t": 10, "type": "$pageview", "pathname": "/pay/INV-123/checkout"},
                {"t": 20, "type": "$autocapture", "event": "click", "element": "button", "text": "Confirm payment"},
                {"t": 22, "type": "$pageview", "pathname": "/pay/INV-123/success"},
                {"t": 30, "type": "$pageleave", "pathname": "/pay/INV-123/success", "converted": True}
            ]
        }
        res = analyze_session(session)
        self.assertFalse(res["flagged"])
        self.assertEqual(res["severity"], "low")

    def test_http_404_error(self):
        """Should flag 404/500 page views as critical."""
        session = {
            "session_id": "test-404",
            "persona": "client",
            "events": [
                {"t": 0, "type": "$pageview", "pathname": "/dashboard"},
                {"t": 5, "type": "$pageview", "pathname": "/reports/missing", "status": 404, "title": "Not Found"}
            ]
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "critical")
        self.assertIn("http_error", res["signals"])

    def test_unhandled_exception(self):
        """Should flag unhandled exception as critical/high."""
        session = {
            "session_id": "test-exception",
            "persona": "client",
            "events": [
                {"t": 0, "type": "$pageview", "pathname": "/imports"},
                {"t": 10, "type": "$exception", "message": "ReferenceError: foo is not defined", "handled": False}
            ]
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "critical")
        self.assertIn("unhandled_exception", res["signals"])

    def test_rage_clicks(self):
        """Should flag rage clicks as high severity."""
        session = {
            "session_id": "test-rage",
            "persona": "client",
            "events": [
                {"t": 0, "type": "$pageview", "pathname": "/reports"},
                {"t": 10, "type": "$rageclick", "element": "button", "text": "Export", "count": 6}
            ]
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "high")
        self.assertIn("rage_click", res["signals"])

    def test_disabled_button_abandonment(self):
        """Should flag debtor sessions where submit button is disabled and they abandon."""
        session = {
            "session_id": "test-disabled-abandon",
            "persona": "debtor",
            "duration_s": 40,
            "events": [
                {"t": 0, "type": "$pageview", "pathname": "/dispute/INV-123"},
                {"t": 10, "type": "$autocapture", "event": "scroll", "depth_pct": 100},
                {"t": 20, "type": "$autocapture", "event": "click", "element": "button", "text": "Submit", "attrs": {"disabled": True}},
                {"t": 40, "type": "$pageleave", "pathname": "/dispute/INV-123", "converted": False}
            ]
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "high")
        self.assertIn("disabled_ui_click", res["signals"])
        self.assertIn("funnel_abandonment_after_friction", res["signals"])

if __name__ == "__main__":
    unittest.main()
