#!/usr/bin/env python3
"""
automated_ux_detector.py
An automated UX bug detector for AgentCollect. Ingests session event traces
from PostHog and flags sessions with potential UX friction/bugs.
"""

import sys
import json
import argparse
from typing import Dict, List, Any, Optional

def analyze_session(session: Dict[str, Any]) -> Dict[str, Any]:
    session_id = session.get("session_id", "unknown")
    persona = session.get("persona", "unknown")
    duration = session.get("duration_s", 0)
    events = session.get("events", [])
    
    flagged = False
    severity_score = 0.0
    signals = []
    reasons = []

    # State tracking variables for chronological scanning
    has_unhandled_exception = False
    has_handled_exception = False
    has_404_or_500 = False
    rage_clicks = []
    dead_clicks = []
    disabled_clicks = []
    pageviews = []
    last_interaction_time = 0
    max_scroll_depth = 0
    clicked_ctas = []
    conversion_status = None # Will store last pageleave 'converted' field if debtor

    for event in events:
        t = event.get("t", 0)
        event_type = event.get("type")
        
        # 1. Pageview tracking
        if event_type == "$pageview":
            pathname = event.get("pathname", "")
            status = event.get("status", 200)
            title = event.get("title", "")
            pageviews.append({"t": t, "pathname": pathname, "status": status, "title": title})
            
            if isinstance(status, int) and status >= 400:
                has_404_or_500 = True
                signals.append("http_error")
                reasons.append(f"HTTP error status {status} encountered on path '{pathname}'")
                severity_score = max(severity_score, 0.95)

        # 2. Autocapture tracking (clicks, scrolls)
        elif event_type == "$autocapture":
            action = event.get("event")
            if action == "click":
                element = event.get("element", "")
                text = event.get("text", "")
                attrs = event.get("attrs", {})
                
                # Check for disabled interactions
                if attrs and attrs.get("disabled") is True:
                    disabled_clicks.append({"t": t, "element": element, "text": text})
                    signals.append("disabled_ui_click")
                    reasons.append(f"User clicked on a disabled {element} ('{text}')")
                    severity_score = max(severity_score, 0.70)
                
                # Track CTAs clicked
                if element in ["button", "a"] or text in ["Process", "Export", "Confirm payment", "Pay now", "Reply / Submit dispute"]:
                    clicked_ctas.append({"t": t, "element": element, "text": text})
                
                last_interaction_time = t
                
            elif action == "scroll":
                depth = event.get("depth_pct", 0)
                if depth > max_scroll_depth:
                    max_scroll_depth = depth

        # 3. Exception tracking
        elif event_type == "$exception":
            message = event.get("message", "")
            handled = event.get("handled", False)
            if not handled:
                has_unhandled_exception = True
                signals.append("unhandled_exception")
                reasons.append(f"Unhandled JS script error: '{message}'")
                severity_score = max(severity_score, 0.90)
            else:
                has_handled_exception = True
                # Handled exceptions alone might not be bugs (e.g., Stripe decline), but we track it
                
        # 4. Rage click tracking
        elif event_type == "$rageclick":
            element = event.get("element", "")
            text = event.get("text", "")
            count = event.get("count", 0)
            rage_clicks.append({"t": t, "element": element, "text": text, "count": count})
            signals.append("rage_click")
            reasons.append(f"Rage clicks ({count} times) on {element} ('{text}')")
            # Rage clicking interactive targets is high severity, decorative parts is medium
            if element in ["button", "a", "input"] or text:
                severity_score = max(severity_score, 0.80)
            else:
                severity_score = max(severity_score, 0.50)

        # 5. Dead click tracking
        elif event_type == "$dead_click":
            element = event.get("element", "")
            text = event.get("text", "")
            dead_clicks.append({"t": t, "element": element, "text": text})
            signals.append("dead_click")
            reasons.append(f"Dead click on {element} ('{text}') did not trigger state change")
            severity_score = max(severity_score, 0.40)

        # 6. Pageleave tracking
        elif event_type == "$pageleave":
            converted = event.get("converted")
            if converted is not None:
                conversion_status = converted

    # --- Session Context Analysis (Generalizing to silent bugs) ---
    
    # Heuristic A: Debtor Funnel Abandonment
    # If debtor spent significant effort (scrolled deeply, clicked buttons, had high duration)
    # but the session ended without conversion (converted == False).
    if persona == "debtor" and conversion_status is False:
        # Check if they had high-intent (e.g., scrolled > 80% or clicked checkout CTAs)
        high_intent = (max_scroll_depth >= 80) or len(clicked_ctas) > 0
        if high_intent:
            # If they had disabled clicks, rage clicks, or dead clicks, it was a blocked friction point.
            if disabled_clicks or rage_clicks or dead_clicks:
                signals.append("funnel_abandonment_after_friction")
                reasons.append("Debtor abandoned funnel after encountering interface friction (disabled/dead clicks)")
                severity_score = max(severity_score, 0.85)
            else:
                # Potential general abandon without explicit errors, but high scroll
                signals.append("funnel_abandonment")
                reasons.append(f"Debtor scrolled {max_scroll_depth}% and clicked buttons, but left without completing transaction")
                severity_score = max(severity_score, 0.45)

    # Heuristic B: Silent Process Stalling (Dashboard/Client pages)
    # A user clicked a processing CTA, but session ended soon after with no navigation or success.
    if persona == "client" and clicked_ctas:
        last_cta = clicked_ctas[-1]
        # If the last event in session was clicking a process/export button and then leaving shortly after
        if duration - last_cta["t"] >= 10:  # Stayed at least 10s after click without further interactions
            # Did we load any new page?
            new_pages = [p for p in pageviews if p["t"] > last_cta["t"]]
            # If they clicked Export/Process and no page view loaded, and session ended or they rage clicked:
            if not new_pages and last_cta["text"] in ["Process", "Export"]:
                if rage_clicks:
                    signals.append("silent_process_freeze")
                    reasons.append(f"Action '{last_cta['text']}' hung, leading to rage clicking and session exit")
                    severity_score = max(severity_score, 0.85)
                else:
                    signals.append("process_stalled")
                    reasons.append(f"User clicked '{last_cta['text']}' but no follow-up page or action occurred before exit")
                    severity_score = max(severity_score, 0.50)

    # Determine flagged status and severity label
    flagged = len(signals) > 0 or severity_score > 0.30

    severity_label = "low"
    if severity_score >= 0.86:
        severity_label = "critical"
    elif severity_score >= 0.61:
        severity_label = "high"
    elif severity_score >= 0.31:
        severity_label = "medium"

    # Deduplicate signals and join reasons into a unified string
    unique_signals = list(dict.fromkeys(signals))
    combined_reason = "; ".join(dict.fromkeys(reasons)) if reasons else "No anomalous UX friction detected"

    return {
        "session_id": session_id,
        "flagged": flagged,
        "severity": severity_label if flagged else "low",
        "signals": unique_signals,
        "reason": combined_reason
    }

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
