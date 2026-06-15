# Clarifications (Round 1)

These are answers to questions candidates often ask. Some of your own questions won't be answered here —
that is intentional. Where we are silent, state your assumption and move on (that is also a signal).

## Target contact
- Priority for "the right contact": **AP / accounts payable** first, then **owner / founder** for small
  businesses, then **CFO / finance lead** for larger ones, then **office manager** as a fallback.
- One good, proven contact per company is enough.
- A **registered-agent address** is an acceptable contact-of-record when no direct AP path exists for a
  no-website or dissolved entity — just label the role honestly and set `needs_human_review`.

## Allowed sources (passive only)
- Public business registries (Secretary of State, D&B/DUNS), the company's own site/socials, archived
  pages, public search. MX / catch-all / SMTP-existence checks **without sending** are fine.
- **Forbidden:** sending any email / SMS / form / call to a real person; paywalled-PII brokers; scraping
  behind a login; storing personal data beyond what the row needs.

## Compliance limits (real — respect them in your design)
- US B2B only. Business contact info only — never personal/home data.
- Record provenance for every value; support opt-out / suppression in your design.
- Do not infer identity from protected characteristics. No dark-pattern scraping.

## Success metric
- **Precision over recall.** A confident, correct, traceable contact is worth more than three guesses. A
  high `needs_human_review` rate on genuinely hard rows is a GOOD result, not a failure.

## Confidence
- Your `confidence_score` (0–1) logic is yours — just make it explainable (more independent agreeing
  sources = higher; single unverifiable source = lower). Below your own threshold → return no contact and
  set `needs_human_review = true` rather than asserting a guess.

## Scope
- Stay in contact-finding. A minimal slice over the 5 rows that shows your resolution approach is enough.
  We care that it would **generalize** to thousands of unseen rows, not that you brute-forced these five.
