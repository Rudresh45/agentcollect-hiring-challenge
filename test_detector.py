#!/usr/bin/env python3
"""
test_detector.py
Unit tests for the automated UX bug detector (detector.py).

Tests are organized by:
  1. Healthy / negative cases (should NOT flag)
  2. Explicit signal triggers (http_error, exception, rage_click, dead_click)
  3. Behavioral heuristics (funnel abandonment, silent freeze, repeated action)
  4. Reasoning correctness — same raw signals, different context → different verdict
"""

import unittest
from detector import analyze_session


class TestHealthySessions(unittest.TestCase):

    def test_successful_payment(self):
        """Debtor completes a clean payment → should not flag."""
        session = {
            "session_id": "t-healthy-pay",
            "persona": "debtor",
            "duration_s": 54,
            "events": [
                {"t": 0,  "type": "$pageview",    "pathname": "/pay/INV-001"},
                {"t": 9,  "type": "$autocapture", "event": "click", "element": "button", "text": "Pay now"},
                {"t": 11, "type": "$pageview",    "pathname": "/pay/INV-001/checkout"},
                {"t": 40, "type": "$autocapture", "event": "click", "element": "button", "text": "Confirm payment"},
                {"t": 42, "type": "$pageview",    "pathname": "/pay/INV-001/success"},
                {"t": 54, "type": "$pageleave",   "pathname": "/pay/INV-001/success", "converted": True},
            ],
        }
        res = analyze_session(session)
        self.assertFalse(res["flagged"])
        self.assertEqual(res["severity"], "low")
        self.assertEqual(res["signals"], [])

    def test_successful_dispute(self):
        """Debtor submits dispute cleanly → should not flag."""
        session = {
            "session_id": "t-healthy-dispute",
            "persona": "debtor",
            "duration_s": 28,
            "events": [
                {"t": 0,  "type": "$pageview",    "pathname": "/dispute/INV-002"},
                {"t": 10, "type": "$autocapture", "event": "scroll", "depth_pct": 90},
                {"t": 18, "type": "$autocapture", "event": "click", "element": "button",
                 "text": "Reply / Submit dispute", "attrs": {"disabled": False}},
                {"t": 19, "type": "$pageview",    "pathname": "/dispute/INV-002/submitted"},
                {"t": 28, "type": "$pageleave",   "pathname": "/dispute/INV-002/submitted", "converted": True},
            ],
        }
        res = analyze_session(session)
        self.assertFalse(res["flagged"])

    def test_client_dashboard_browse(self):
        """Client browses multiple pages with no errors → should not flag."""
        session = {
            "session_id": "t-healthy-client",
            "persona": "client",
            "duration_s": 33,
            "events": [
                {"t": 0,  "type": "$pageview",    "pathname": "/dashboard"},
                {"t": 4,  "type": "$autocapture", "event": "click", "element": "a", "text": "Cases"},
                {"t": 5,  "type": "$pageview",    "pathname": "/cases"},
                {"t": 20, "type": "$autocapture", "event": "click", "element": "tr", "text": "FedEx"},
                {"t": 21, "type": "$pageview",    "pathname": "/cases/123"},
                {"t": 33, "type": "$pageleave",   "pathname": "/cases/123"},
            ],
        }
        res = analyze_session(session)
        self.assertFalse(res["flagged"])


class TestExplicitSignals(unittest.TestCase):

    def test_http_404_is_critical(self):
        """$pageview with status 404 → critical."""
        session = {
            "session_id": "t-404",
            "persona": "client",
            "duration_s": 20,
            "events": [
                {"t": 0, "type": "$pageview", "pathname": "/dashboard"},
                {"t": 5, "type": "$pageview", "pathname": "/reports/recovery",
                 "status": 404, "title": "404 - Page not found"},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "critical")
        self.assertIn("http_error", res["signals"])

    def test_http_500_is_critical(self):
        """$pageview with status 500 → critical."""
        session = {
            "session_id": "t-500",
            "persona": "client",
            "duration_s": 10,
            "events": [
                {"t": 0, "type": "$pageview", "pathname": "/imports", "status": 500},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "critical")

    def test_unhandled_exception_is_critical(self):
        """Unhandled JS crash → critical."""
        session = {
            "session_id": "t-exception",
            "persona": "client",
            "duration_s": 20,
            "events": [
                {"t": 0,  "type": "$pageview",   "pathname": "/imports"},
                {"t": 10, "type": "$exception",  "message": "ReferenceError: foo", "handled": False},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "critical")
        self.assertIn("unhandled_exception", res["signals"])

    def test_handled_payment_decline_alone_not_flagged(self):
        """
        Handled Stripe card_declined is EXPECTED behavior — should NOT flag the
        session just because a payment failed.  This tests the reasoning gate.
        """
        session = {
            "session_id": "t-card-declined-only",
            "persona": "debtor",
            "duration_s": 40,
            "events": [
                {"t": 0,  "type": "$pageview",    "pathname": "/pay/INV-003"},
                {"t": 5,  "type": "$autocapture", "event": "click", "element": "button", "text": "Pay now"},
                {"t": 6,  "type": "$pageview",    "pathname": "/pay/INV-003/checkout"},
                {"t": 20, "type": "$autocapture", "event": "click", "element": "button", "text": "Confirm payment"},
                {"t": 21, "type": "$exception",   "message": "Stripe error: card_declined", "handled": True},
                {"t": 40, "type": "$pageleave",   "pathname": "/pay/INV-003/checkout", "converted": False},
            ],
        }
        res = analyze_session(session)
        # A card decline is not a UX bug — the user's card failed, not the UI.
        self.assertFalse(res["flagged"], "Should NOT flag: handled payment decline is expected behavior")
        self.assertNotIn("funnel_abandonment_after_friction", res["signals"])

    def test_rage_click_on_action_button_is_high(self):
        """Rage click on a button → high severity."""
        session = {
            "session_id": "t-rage-btn",
            "persona": "client",
            "duration_s": 20,
            "events": [
                {"t": 0,  "type": "$pageview",   "pathname": "/reports"},
                {"t": 10, "type": "$rageclick",  "element": "button", "text": "Export", "count": 6},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "high")
        self.assertIn("rage_click", res["signals"])

    def test_dead_click_on_help_link_flagged(self):
        """Dead click on a 'Need help?' link → flagged (user in distress, no escape)."""
        session = {
            "session_id": "t-dead-help",
            "persona": "debtor",
            "duration_s": 30,
            "events": [
                {"t": 0,  "type": "$pageview",   "pathname": "/pay/INV-004/checkout"},
                {"t": 20, "type": "$dead_click", "element": "a", "text": "Need help?"},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertIn("dead_click", res["signals"])
        self.assertIn("dead_help_link", res["signals"])


class TestBehavioralHeuristics(unittest.TestCase):

    def test_disabled_button_funnel_abandonment(self):
        """
        Debtor scrolls 100%, hits a disabled Submit button, rage-clicks, abandons.
        → Should flag funnel_abandonment_after_friction.
        """
        session = {
            "session_id": "t-disabled-abandon",
            "persona": "debtor",
            "duration_s": 40,
            "events": [
                {"t": 0,  "type": "$pageview",    "pathname": "/dispute/INV-005"},
                {"t": 10, "type": "$autocapture", "event": "scroll", "depth_pct": 100},
                {"t": 20, "type": "$autocapture", "event": "click",  "element": "button",
                 "text": "Submit", "attrs": {"disabled": True}},
                {"t": 21, "type": "$rageclick",   "element": "button", "text": "Submit", "count": 4},
                {"t": 40, "type": "$pageleave",   "pathname": "/dispute/INV-005", "converted": False},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertIn("disabled_ui_click", res["signals"])
        self.assertIn("rage_click", res["signals"])
        self.assertIn("funnel_abandonment_after_friction", res["signals"])
        # Score: max(0.70 disabled, 0.85 rage-on-button, 0.85 funnel) = 0.85 → "high"
        self.assertIn(res["severity"], ("high", "critical"))

    def test_payment_decline_then_dead_help_is_flagged(self):
        """
        Debtor's card is declined (expected), then clicks a dead 'Need help?' link.
        The card decline itself is NOT a UX bug, but the broken help link IS.
        → Should flag dead_click + dead_help_link but NOT funnel_abandonment_after_friction.
        """
        session = {
            "session_id": "t-decline-dead-help",
            "persona": "debtor",
            "duration_s": 95,
            "events": [
                {"t": 0,  "type": "$pageview",    "pathname": "/pay/INV-006"},
                {"t": 8,  "type": "$autocapture", "event": "click", "element": "button", "text": "Pay now"},
                {"t": 10, "type": "$pageview",    "pathname": "/pay/INV-006/checkout"},
                {"t": 35, "type": "$autocapture", "event": "click", "element": "button", "text": "Confirm payment"},
                {"t": 36, "type": "$exception",   "message": "Stripe error: card_declined", "handled": True},
                {"t": 50, "type": "$autocapture", "event": "click", "element": "button", "text": "Confirm payment"},
                {"t": 51, "type": "$exception",   "message": "Stripe error: card_declined", "handled": True},
                {"t": 70, "type": "$dead_click",  "element": "a", "text": "Need help?"},
                {"t": 95, "type": "$pageleave",   "pathname": "/pay/INV-006/checkout", "converted": False},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertIn("dead_help_link", res["signals"],
                      "Dead help link should be flagged — user is stuck and seeking support")
        self.assertNotIn("funnel_abandonment_after_friction", res["signals"],
                         "Should NOT flag funnel abandonment — root cause is card decline, not UI bug")

    def test_silent_process_freeze_generalized(self):
        """
        Client clicks an arbitrary action button (not just 'Export'/'Process'),
        waits >10s, no new page loads, then rage-clicks and leaves.
        → Should detect silent_process_freeze without needing the button text hardcoded.
        """
        session = {
            "session_id": "t-freeze-generic",
            "persona": "client",
            "duration_s": 150,
            "events": [
                {"t": 0,   "type": "$pageview",    "pathname": "/imports"},
                {"t": 20,  "type": "$autocapture", "event": "click", "element": "button", "text": "Run sync"},
                {"t": 120, "type": "$rageclick",   "element": "button", "text": "Run sync", "count": 5},
                {"t": 150, "type": "$pageleave",   "pathname": "/imports"},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertIn("silent_process_freeze", res["signals"])

    def test_repeated_identical_action_no_progress(self):
        """
        Client clicks the same button twice with no page change between.
        → Should flag repeated_identical_action.
        """
        session = {
            "session_id": "t-repeat-action",
            "persona": "client",
            "duration_s": 200,
            "events": [
                {"t": 0,   "type": "$pageview",    "pathname": "/reports"},
                {"t": 40,  "type": "$autocapture", "event": "click", "element": "button", "text": "Generate"},
                {"t": 120, "type": "$autocapture", "event": "click", "element": "button", "text": "Generate"},
                {"t": 200, "type": "$pageleave",   "pathname": "/reports"},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertIn("repeated_identical_action", res["signals"])

    def test_funnel_abandonment_without_friction(self):
        """
        Debtor scrolls 90% but no friction (disabled/dead/rage) — should flag
        softer funnel_abandonment (not funnel_abandonment_after_friction).
        """
        session = {
            "session_id": "t-abandon-no-friction",
            "persona": "debtor",
            "duration_s": 60,
            "events": [
                {"t": 0,  "type": "$pageview",    "pathname": "/pay/INV-007"},
                {"t": 20, "type": "$autocapture", "event": "scroll", "depth_pct": 90},
                {"t": 60, "type": "$pageleave",   "pathname": "/pay/INV-007", "converted": False},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertIn("funnel_abandonment", res["signals"])
        self.assertNotIn("funnel_abandonment_after_friction", res["signals"])


class TestGeneralization(unittest.TestCase):
    """
    These tests verify the detector works on signals it has not seen before —
    i.e. no hardcoded element text or page names are required.
    """

    def test_novel_button_text_still_detected(self):
        """
        A brand-new action button ('Reconcile accounts') that was never in training data
        should still trigger silent_process_freeze if the behavioural pattern matches.
        """
        session = {
            "session_id": "t-novel-button",
            "persona": "client",
            "duration_s": 100,
            "events": [
                {"t": 0,   "type": "$pageview",    "pathname": "/cases"},
                {"t": 10,  "type": "$autocapture", "event": "click",
                 "element": "button", "text": "Reconcile accounts"},
                {"t": 80,  "type": "$rageclick",   "element": "button",
                 "text": "Reconcile accounts", "count": 3},
                {"t": 100, "type": "$pageleave",   "pathname": "/cases"},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertIn("silent_process_freeze", res["signals"],
                      "Novel action button should still be caught by generalised heuristic")

    def test_novel_404_path_detected(self):
        """A 404 on any path — even one never seen before — should be critical."""
        session = {
            "session_id": "t-novel-404",
            "persona": "client",
            "duration_s": 10,
            "events": [
                {"t": 0, "type": "$pageview", "pathname": "/analytics/cashflow", "status": 404},
            ],
        }
        res = analyze_session(session)
        self.assertTrue(res["flagged"])
        self.assertEqual(res["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
