"""SQLite access layer (stdlib sqlite3, no ORM) for the Nx01 Platform."""
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get(
    "NX01_DB_PATH", os.path.join(BASE_DIR, "data", "platform.db")
)

# Date the Intel Vault contents were verified against their sources
# (Bug Bounty Intel Vault build, 2026-11-25). Used as the seeded
# `checked_at` for vault rows that predate the v1.1 contract surface.
VAULT_CHECKED_AT = "2026-11-25"

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    tagline     TEXT,
    summary     TEXT,
    skills      TEXT,              -- comma-separated skill tags
    status      TEXT NOT NULL DEFAULT 'live',   -- live | proposed
    is_hero     INTEGER NOT NULL DEFAULT 0,
    visibility  TEXT DEFAULT 'public',          -- public | private
    repo_url    TEXT,
    note        TEXT,
    attribution TEXT               -- v1.1: contract Project.attribution
);

CREATE TABLE IF NOT EXISTS vault_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,     -- payout | writeup | tip | research (+ contract kinds on write)
    title       TEXT NOT NULL,
    category    TEXT,              -- vuln class / section
    program     TEXT,              -- payouts only
    summary     TEXT,
    amount_usd  REAL,              -- payouts only
    source_url  TEXT,
    verified    INTEGER NOT NULL DEFAULT 1,
    checked_at  TEXT,              -- v1.1: contract KnowledgeEntry.checked_at (YYYY-MM-DD)
    verification TEXT,             -- v1.1: VerificationLabel (tested|documented|untested)
    tags        TEXT               -- v1.1: JSON array of strings
);

-- Zero Track Lab bounty-outcome ledger (v1 concept; API stays at /api/ledger).
-- NOT the contract's /ledger — see run_ledger below and V1.1-REPORT.md.
CREATE TABLE IF NOT EXISTS ledger_entries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id        TEXT UNIQUE NOT NULL,
    recorded_at         TEXT,
    run_id              TEXT,
    program_platform    TEXT,
    program_handle      TEXT,
    asset               TEXT,
    vuln_class          TEXT,
    wing                TEXT,
    gate_verdict        TEXT,      -- pass | reject
    gate_reject_reason  TEXT,
    verifier_type       TEXT,
    human_review_action TEXT,
    program_verdict     TEXT,      -- resolved | duplicate | informative | n/a | NULL
    program_severity    TEXT,
    bounty_usd          REAL,
    cost_infra_usd      REAL,
    is_example          INTEGER NOT NULL DEFAULT 0,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS metrics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    month       TEXT NOT NULL,     -- YYYY-MM
    name        TEXT NOT NULL,     -- e.g. valid_rate, gate_precision
    value       REAL,
    numerator   REAL,
    denominator REAL,
    notes       TEXT,
    UNIQUE(month, name)
);

-- v1.1 contract surface -------------------------------------------------
-- Evidence attached to a project (contract Evidence schema).
CREATE TABLE IF NOT EXISTS evidence (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug TEXT NOT NULL,
    type        TEXT NOT NULL,     -- commit | test-output | video | metric | doc
    url         TEXT NOT NULL,
    note        TEXT,
    recorded_at TEXT NOT NULL      -- YYYY-MM-DD
);

-- Reproducible metric runs attached to a project (contract MetricRun).
CREATE TABLE IF NOT EXISTS metric_runs (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug            TEXT NOT NULL,
    name                    TEXT NOT NULL,
    baseline                TEXT NOT NULL,
    result                  TEXT NOT NULL,
    method                  TEXT NOT NULL,
    run_command             TEXT NOT NULL,
    environment             TEXT,
    pass_fail_criteria      TEXT NOT NULL,
    declared_failing_cases  TEXT NOT NULL,
    run_at                  TEXT NOT NULL   -- ISO date-time
);

-- Contract /ledger: the lab *run log* (LedgerEntry). Deliberately a
-- separate table from ledger_entries (the bounty-outcome ledger) —
-- the two share a word, not a domain object. See V1.1-REPORT.md.
CREATE TABLE IF NOT EXISTS run_ledger (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug TEXT NOT NULL,
    action       TEXT NOT NULL,
    result       TEXT NOT NULL,    -- pass | fail | blocked
    run_command  TEXT NOT NULL,
    evidence_url TEXT,
    ran_at       TEXT NOT NULL     -- ISO date-time
);

-- Mutual-review records (contract ReviewRecordIn). Write-only surface:
-- the contract defines POST /reviews and no GET.
CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject     TEXT NOT NULL,
    reviewer    TEXT NOT NULL,     -- instinct | elkaref
    decision    TEXT NOT NULL,     -- accepted | rejected | accepted-with-notes
    reason      TEXT NOT NULL,
    reviewed_at TEXT NOT NULL      -- ISO date-time
);
"""

# Columns added after v1 shipped; applied additively to existing DBs.
_ADDED_COLUMNS = {
    "projects": [("attribution", "TEXT")],
    "vault_entries": [
        ("checked_at", "TEXT"),
        ("verification", "TEXT"),
        ("tags", "TEXT"),
    ],
}

# Dedicated attribution for the one project whose origin is a third-party
# fork — promoted out of the free-text `note` (where v1 kept it) into the
# contract's first-class `attribution` field. Wording mirrors the audit
# correction: the repo IS officially marked as a fork of AwareXone's
# project; README/branding cleanup is still pending.
ABH_ATTRIBUTION = (
    "Fork of AwareXone/Agentic-Bug-Hunter (the repo is officially marked "
    "as a fork). README, license and links still belong to the upstream "
    "project — branding cleanup pending; the owner's own contribution is "
    "his fork work on top of upstream."
)


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _columns(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def migrate_v11(conn: sqlite3.Connection) -> None:
    """Additive, idempotent v1.1 migration: new columns + backfills.

    Never drops or rewrites existing data. Backfills only fill NULLs:
    - vault checked_at  <- the vault verification date (2026-11-25)
    - vault verification <- documented when verified=1, else untested
      (interim mapping from CONTRACT-GAPS fix 6: source-verified rows are
      *documented*; nothing seeded claims to be hands-on *tested*)
    - vault tags <- [category] when a category exists, else []
    - projects.attribution <- the ABH fork attribution (from its note)
    - evidence <- one `doc` evidence row per project that has a repo_url
      (the repository itself, verified in the 2026-11-25 project audit)
    """
    for table, cols in _ADDED_COLUMNS.items():
        existing = _columns(conn, table)
        for name, decl in cols:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")

    conn.execute(
        "UPDATE vault_entries SET checked_at = ? WHERE checked_at IS NULL",
        (VAULT_CHECKED_AT,))
    conn.execute(
        "UPDATE vault_entries SET verification = "
        "CASE WHEN verified = 1 THEN 'documented' ELSE 'untested' END "
        "WHERE verification IS NULL")
    for row in conn.execute(
            "SELECT id, category FROM vault_entries WHERE tags IS NULL"):
        tags = [row[1]] if row[1] else []
        conn.execute("UPDATE vault_entries SET tags = ? WHERE id = ?",
                     (json.dumps(tags), row[0]))

    conn.execute(
        "UPDATE projects SET attribution = ? "
        "WHERE slug = 'agentic-bug-hunter' AND attribution IS NULL",
        (ABH_ATTRIBUTION,))

    conn.execute(
        "INSERT INTO evidence (project_slug, type, url, note, recorded_at) "
        "SELECT slug, 'doc', repo_url, "
        "'GitHub repository — existence verified in the 2026-11-25 "
        "project audit', ? FROM projects WHERE repo_url IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM evidence e "
        "WHERE e.project_slug = projects.slug)",
        (VAULT_CHECKED_AT,))
    conn.commit()


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
    migrate_v11(conn)


def rows_to_dicts(rows):
    return [dict(r) for r in rows]
