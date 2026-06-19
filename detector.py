
"""
detector.py
Automated UX Bug Detector for AgentCollect.

Ingests session event traces (PostHog JSONL) and flags sessions with UX friction/bugs.

Design philosophy:
  - We do NOT hardcode known bug pages or specific element text. We model expected
    *behavioral invariants* per persona surface and flag deviations.
  - Before trusting a raw signal (rage click, dead click, abandon), we ask: "Could this
    be intended?" A Stripe card decline is expected. A disabled Submit button on a fully
    filled form is not.
  - We separate debtor pages (strict linear funnel) from client dashboard (exploratory)
    because the same signal means different things on each surface.
  - PII: We never forward raw event arrays to external systems. Only derived
    metadata (session_id, signal names, severity) leaves this process.
"""

import sys
import json
import re
import argparse
from typing import Dict, List, Any, Optional, Tuple


# ---------------------------------------------------------------------------
# Surface classification helpers
# ---------------------------------------------------------------------------

DEBTOR_PATH_PREFIXES = ("/pay/", "/dispute/")
CLIENT_PATH_PREFIXES = ("/dashboard", "/reports", "/cases", "/imports", "/settings")

def classify_surface(pathname: str) -> str:
    """Return 'debtor', 'client', or 'unknown' for a given pathname."""
    if any(pathname.startswith(p) for p in DEBTOR_PATH_PREFIXES):
        return "debtor"
    if any(pathname.startswith(p) for p in CLIENT_PATH_PREFIXES):
        return "client"
    return "unknown"


# ---------------------------------------------------------------------------
# Generalised heuristics — no hardcoded element text or page names
# ---------------------------------------------------------------------------

def is_high_intent_action(element: str, text: str) -> bool:
    """
    Determine if a click target is a *high-intent action* without hardcoding
    specific labels. We use structural heuristics:
      - The element is a button or submit input (not a link/anchor used for nav).
      - Optional: the text is not purely navigational ("back", "cancel", "close").
    This generalizes to action verbs we've never seen before.
    """
    if element not in ("button", "input[type=submit]", "input[type=button]"):
        return False
    # Navigation/dismissal words — low intent
    nav_words = re.compile(
        r"^\s*(back|cancel|close|home|menu|log.?out|sign.?out|help|faq|"
        r"learn more|read more|see more|view|details)\s*$",
        re.IGNORECASE,
    )
    if nav_words.match(text or ""):
        return False
    return True


def is_help_or_support_element(element: str, text: str) -> bool:
    """Identify help/support links that are expected to navigate somewhere."""
    if element not in ("a", "button", "span"):
        return False
    help_pattern = re.compile(
        r"(help|support|contact|faq|chat|guide|learn|tutorial|question|\?)",
        re.IGNORECASE,
    )
    return bool(help_pattern.search(text or ""))


def is_navigation_link(element: str, text: str) -> bool:
    """Detect nav links (sidebar, topbar) — rage-clicking these is lower severity."""
    return element == "a" and bool(text)


# ---------------------------------------------------------------------------
# Core session analyser
# ---------------------------------------------------------------------------

def analyze_session(session: Dict[str, Any]) -> Dict[str, Any]:
    session_id = session.get("session_id", "unknown")
    persona = session.get("persona", "unknown")
    duration = session.get("duration_s", 0)
    events = session.get("events", [])

    severity_score = 0.0
    signals: List[str] = []
    reasons: List[str] = []

    # ── per-event state ────────────────────────────────────────────────────
    has_unhandled_exception = False
    has_payment_declined = False        # handled Stripe/payment error
    pageviews: List[Dict] = []
    rage_clicks: List[Dict] = []
    dead_clicks: List[Dict] = []
    disabled_clicks: List[Dict] = []
    high_intent_clicks: List[Dict] = []  # generalized: buttons that expect a result
    all_clicks: List[Dict] = []
    max_scroll_depth = 0
    conversion_status: Optional[bool] = None
    last_page_surface = "unknown"

    # ── chronological scan ─────────────────────────────────────────────────
    for event in events:
        t = event.get("t", 0)
        event_type = event.get("type")

        # ── $pageview ──────────────────────────────────────────────────────
        if event_type == "$pageview":
            pathname = event.get("pathname", "")
            status = event.get("status", 200)
            title = event.get("title", "")
            surface = classify_surface(pathname)
            if surface != "unknown":
                last_page_surface = surface
            pageviews.append({"t": t, "pathname": pathname, "status": status,
                               "surface": surface, "title": title})

            if isinstance(status, int) and status >= 400:
                signals.append("http_error")
                reasons.append(
                    f"HTTP {status} on '{pathname}'"
                    + (f" ('{title}')" if title else "")
                )
                severity_score = max(severity_score, 0.95)

        # ── $autocapture ───────────────────────────────────────────────────
        elif event_type == "$autocapture":
            action = event.get("event")

            if action == "click":
                element = event.get("element", "")
                text = event.get("text", "") or ""
                attrs = event.get("attrs") or {}
                click_rec = {"t": t, "element": element, "text": text}
                all_clicks.append(click_rec)

                # Disabled element clicks
                if attrs.get("disabled") is True:
                    disabled_clicks.append(click_rec)
                    signals.append("disabled_ui_click")
                    reasons.append(
                        f"Click on disabled {element} ('{text}')"
                    )
                    severity_score = max(severity_score, 0.70)

                # High-intent action button tracking (generalized — no text whitelist)
                if is_high_intent_action(element, text):
                    high_intent_clicks.append(click_rec)

            elif action == "scroll":
                depth = event.get("depth_pct", 0)
                if depth > max_scroll_depth:
                    max_scroll_depth = depth

        # ── $exception ─────────────────────────────────────────────────────
        elif event_type == "$exception":
            message = event.get("message", "")
            handled = event.get("handled", False)

            # Distinguish payment declines (expected) from true crashes
            is_payment_decline = bool(re.search(
                r"(card_declined|insufficient_funds|payment|stripe|paypal|"
                r"transaction.*fail|declined)",
                message, re.IGNORECASE,
            ))

            if not handled:
                has_unhandled_exception = True
                signals.append("unhandled_exception")
                reasons.append(f"Unhandled JS error: '{message}'")
                severity_score = max(severity_score, 0.90)
            elif handled and is_payment_decline:
                has_payment_declined = True
                # Handled payment declines are *expected* UX paths — not flagged alone.
                # We track them to avoid falsely attributing subsequent abandonment to
                # a UI bug when the real cause is card failure.
            # Other handled exceptions: track but don't flag — user-input validation etc.

        # ── $rageclick ─────────────────────────────────────────────────────
        elif event_type == "$rageclick":
            element = event.get("element", "")
            text = event.get("text", "") or ""
            count = event.get("count", 0)
            rage_clicks.append({"t": t, "element": element, "text": text, "count": count})
            signals.append("rage_click")
            reasons.append(f"Rage clicks ({count}×) on {element} ('{text}')")

            # Higher severity on actionable targets; lower on nav links
            if is_high_intent_action(element, text):
                severity_score = max(severity_score, 0.85)
            elif is_navigation_link(element, text):
                severity_score = max(severity_score, 0.75)
            else:
                severity_score = max(severity_score, 0.55)

        # ── $dead_click ────────────────────────────────────────────────────
        elif event_type == "$dead_click":
            element = event.get("element", "")
            text = event.get("text", "") or ""
            dead_clicks.append({"t": t, "element": element, "text": text})
            signals.append("dead_click")
            reasons.append(f"Dead click on {element} ('{text}') — no state change")

            # Dead click on a help/support link is particularly bad: user is stuck
            # and actively seeking assistance but gets nothing.
            if is_help_or_support_element(element, text):
                severity_score = max(severity_score, 0.65)
                signals.append("dead_help_link")
                reasons.append(
                    f"Help/support link ('{text}') is dead — user in distress, "
                    "no escape route"
                )
            else:
                severity_score = max(severity_score, 0.40)

        # ── $pageleave ─────────────────────────────────────────────────────
        elif event_type == "$pageleave":
            converted = event.get("converted")
            if converted is not None:
                conversion_status = converted

    # ── Post-scan heuristics ───────────────────────────────────────────────

    # Heuristic A: Debtor Funnel Abandonment after UI Friction
    # We only raise this if the abandonment is plausibly caused by a UI bug, NOT by a
    # legitimate payment failure (e.g. card declined) which is an expected user-error path.
    #
    # Reasoning gate:
    #   - If the user had handled payment declines, the primary exit reason is the card
    #     failure, not a UI bug.  A dead help link or other secondary friction is still
    #     flagged separately (dead_click / dead_help_link), but we do NOT also flag
    #     funnel_abandonment_after_friction — that would conflate two different root causes.
    #   - Only raise funnel_abandonment_after_friction when UI friction (disabled button,
    #     rage-click on submit, dead non-help link) is the most plausible exit cause AND
    #     there was no handled payment decline.
    if persona == "debtor" and conversion_status is False:
        high_intent = (max_scroll_depth >= 80) or bool(high_intent_clicks)
        # Friction that directly blocks submission — distinguished from a dead help link
        # (which is a secondary bug, not the primary funnel blocker).
        direct_submit_friction = bool(disabled_clicks or rage_clicks)
        # A dead click on a non-help element (e.g. a broken nav item) can also block the funnel.
        blocking_dead_clicks = [d for d in dead_clicks if not is_help_or_support_element(d["element"], d["text"])]

        # Primary exit cause: payment declined, not a UI bug
        payment_was_root_cause = has_payment_declined and not direct_submit_friction and not blocking_dead_clicks

        if high_intent and (direct_submit_friction or blocking_dead_clicks) and not payment_was_root_cause:
            signals.append("funnel_abandonment_after_friction")
            reasons.append(
                "Debtor abandoned funnel after UI friction "
                "(disabled submit or blocking dead element, not a payment decline)"
            )
            severity_score = max(severity_score, 0.85)
        elif high_intent and not direct_submit_friction and not blocking_dead_clicks and not has_payment_declined:
            # Unexplained drop-off — worth noting but lower confidence
            signals.append("funnel_abandonment")
            reasons.append(
                f"Debtor scrolled {max_scroll_depth}% and interacted with action "
                "buttons but left without converting — no obvious friction captured"
            )
            severity_score = max(severity_score, 0.40)

    # Heuristic B: Silent Process Freeze (Client dashboard)
    # Generalized: any high-intent button click followed by >= 10s of inactivity
    # (no new pageview, no further interactions) before session end indicates a stall.
    # We do NOT require "Export" or "Process" to be in the text — any action button qualifies.
    if persona == "client" and high_intent_clicks:
        last_action = high_intent_clicks[-1]
        action_t = last_action["t"]
        idle_window = duration - action_t

        # Was there any subsequent pageview after the action?
        pages_after = [p for p in pageviews if p["t"] > action_t]
        # Was there any further click after the action?
        clicks_after = [c for c in all_clicks if c["t"] > action_t]

        if idle_window >= 10 and not pages_after and not clicks_after:
            if rage_clicks:
                signals.append("silent_process_freeze")
                reasons.append(
                    f"Action '{last_action['text']}' produced no page change or "
                    f"feedback after {idle_window}s; user rage-clicked and exited"
                )
                severity_score = max(severity_score, 0.85)
            else:
                signals.append("process_stalled")
                reasons.append(
                    f"Action '{last_action['text']}' produced no follow-up "
                    f"after {idle_window}s — possible silent hang"
                )
                severity_score = max(severity_score, 0.50)

    # Heuristic C: Repeated identical high-intent action without progress
    # Generalizes to any button a user clicks multiple times in sequence without
    # an intervening page navigation OR error response — signals the action silently does nothing.
    #
    # Key reasoning: if the action DID respond (even with an error — e.g. $exception after click),
    # a retry is EXPECTED behaviour (user correcting their input / retrying after card decline).
    # We only flag when the action produced NO response at all.
    if high_intent_clicks and len(high_intent_clicks) >= 2:
        for i in range(1, len(high_intent_clicks)):
            prev = high_intent_clicks[i - 1]
            curr = high_intent_clicks[i]
            if curr["text"] == prev["text"] and curr["element"] == prev["element"]:
                # Was there any page nav between the two clicks?
                nav_between = any(prev["t"] < p["t"] < curr["t"] for p in pageviews)
                # Was there ANY $exception between the two clicks? (action responded with error)
                exception_between = any(
                    prev["t"] < e.get("t", 0) < curr["t"]
                    for e in events
                    if e.get("type") == "$exception"
                )
                if not nav_between and not exception_between:
                    if "repeated_identical_action" not in signals:
                        signals.append("repeated_identical_action")
                        reasons.append(
                            f"'{curr['text']}' clicked multiple times without any "
                            "response (no page change, no error) — action silently does nothing"
                        )
                        severity_score = max(severity_score, 0.55)

    # ── Derive final output ────────────────────────────────────────────────
    flagged = severity_score > 0.30

    if severity_score >= 0.86:
        severity_label = "critical"
    elif severity_score >= 0.61:
        severity_label = "high"
    elif severity_score >= 0.31:
        severity_label = "medium"
    else:
        severity_label = "low"

    # Deduplicate while preserving insertion order
    unique_signals = list(dict.fromkeys(signals))
    combined_reason = "; ".join(dict.fromkeys(reasons)) if reasons else "No anomalous UX friction detected"

    return {
        "session_id": session_id,
        "flagged": flagged,
        "severity": severity_label if flagged else "low",
        "signals": unique_signals,
        "reason": combined_reason,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AgentCollect UX Bug Detector")
    parser.add_argument("input_file", help="Path to session event traces (JSONL format)")
    args = parser.parse_args()

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    session = json.loads(line)
                    result = analyze_session(session)
                    print(json.dumps(result))
                except json.JSONDecodeError:
                    print(json.dumps({"error": "Failed to parse JSON line"}), file=sys.stderr)
    except FileNotFoundError:
        print(json.dumps({"error": f"Input file not found: {args.input_file}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
