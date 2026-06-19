# ABOUT.md — Candidate Profile & Project Experience

This document details my engineering approach, working style with AI systems, and experience.

---

## Why this role

Building AI-native software systems that can interpret complex user behavior and automate decisions is one of the most compelling frontiers in engineering today. AgentCollect's mission to resolve collection and disputes via intelligent communication, combined with a plan-first and AI-assisted culture, is exactly the environment where I thrive. I enjoy working on highly practical, transactional software where design decisions directly impact business outcomes.

---

## How you work with AI tools

I treat AI tools (such as Claude Code, cursor, and copilot) as active pair-programming partners, not magic boxes. My approach consists of:
* **Plan First:** I always establish design boundaries, file structures, and data flows before allowing the AI to generate code. This prevents bloated code and stray files.
* **Rigorous Review:** I scrutinize AI suggestions for performance regressions, edge cases, error handling, and security leaks.
* **Deterministic Verification:** I write tests and verify the code manually. If the AI proposes a solution, it must be validated under real conditions.

---

## Your last project (structured)

* **One ambiguity you faced and how you resolved it:**
  * *Context:* Building an analytics collector for dynamic, single-page client dashboards. It was ambiguous how to define "failed user action" when buttons did not perform database mutations.
  * *Resolution:* I established a heuristic mapping system that tracked element focus, click count, and subsequent user navigation within a 5-second window to detect dead-end routes, validating it with sample user flows.
* **One tradeoff you made and why:**
  * *Tradeoff:* Opted for deterministic rule-based triggers (regular expressions, status-code matches, attribute checks) over a sequence-to-sequence ML model.
  * *Rationale:* Tradeoff of marginal classification accuracy for 100% explainable alerts, low latency, and zero dependency overhead.
* **One mistake you made and what you changed:**
  * *Mistake:* Directly attaching event listeners to individual DOM elements in a dynamic list, leading to memory leaks when elements were added/removed.
  * *Correction:* Refactored to event delegation, registering a single event listener on the parent container to handle bubbles.
* **One review comment that made you change your mind:**
  * *Comment:* "We are capturing raw element labels in telemetry, which might accidentally store credit card numbers if users type them into search/filter inputs."
  * *Change:* Redesigned the capturing layer to exclude elements containing numbers or specific field label matches (e.g., card, cvc) from text capture entirely.

---

## Anything you'd improve about THIS challenge or our CLAUDE.md

* The challenge structure is excellent; assessing reasoning and planning prior to coding is highly effective.
* To improve, the `challenge/PLAN.template.md` at the root corresponds to the legacy contact-finder challenge, which could confuse candidates. Updating the template or removing legacy templates would make the repository cleaner.
