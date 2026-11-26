# Engineering Ledger — Knowledge Platform

## Origin
Moved out of `security-youtube-channel-plan/coordination/platform/` into this standalone repo on 2026-11-26 (owner decision, Telegram batch item 8). The channel repo is now content-only; this repo is the canonical location. The internal design-discussion doc was moved to the private project-brain imports (it documents an unverified-channel negotiation; not portfolio material).

## Verification state (honest labels)
- 17/17 offline contract checks re-run at publication 2026-11-26: 9 schema + 8 parity, PASS (pytest, contract/).
- 8 live acceptance + 8 negative checks: author-written (Instinct), 🟡 awaiting independent review. Not re-run at publication.
- The platform v1.1 deployment was independently verified live on 2026-11-26 (see project-brain).
- Counting note: the "25 total" = 9 schema + 8 parity + 8 acceptance. Older "17 offline + 8 live" wording counted differently; README is the canonical count.

## Data
- `platform/data/platform.db` is a SEEDED snapshot for the free-tier deploy: 20 project cards, 73 public bounty-payout vault entries (all with public source URLs), fictional EXAMPLE ledger rows (marked). PII scan at publication: 0 hits. No secrets (scan at publication: only content-text matches).

## Provenance
Agent-assisted (Instinct) under owner direction. The project originated from an unverified counterpart proposal; owner-confirmed scope is portfolio/interview support. Attribution column in the DB marks forked upstream work honestly (Agentic-Bug-Hunter).
