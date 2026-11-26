"""v1.1 contract surface — Instinct's platform contract at root paths.

Implements the canonical contract (Tawffik/knowledge-platform,
contract/openapi.yaml): 5 paths / 7 operations. The v1 API under /api
is untouched; this router is a second, contract-shaped view over the
same database, plus the contract's write surface (POST /knowledge,
POST /ledger, POST /reviews).

Boundary translations (documented in V1.1-REPORT.md):
- Project.title      <- projects.name
- Project.skills     <- projects.skills CSV split into an array
- Project.status     <- live->active, proposed->wip (DB values unchanged)
- KnowledgeEntry     <- vault_entries (body<-summary, verification label
                        stored on the row since v1.1; payouts/tips are a
                        declared read-side extension of the kind enum)
- LedgerEntry        <- run_ledger, the contract's lab *run log*.
                        The local bounty-outcome ledger is a different
                        entity and keeps its v1 home at /api/ledger.
"""
import json

from fastapi import APIRouter, HTTPException, Path, Query

from app.db import connect, rows_to_dicts
from app.models import (
    ContractStatus,
    KnowledgeEntry,
    KnowledgeEntryIn,
    LedgerEntry,
    LedgerEntryIn,
    Project,
    ProjectDetail,
    ReviewRecord,
    ReviewRecordIn,
    VerificationLabel,
)

router = APIRouter(tags=["contract"])

STATUS_TO_CONTRACT = {"live": "active", "proposed": "wip",
                      "archived": "archived"}
STATUS_FROM_CONTRACT = {v: k for k, v in STATUS_TO_CONTRACT.items()}
SLUG_PATTERN = "^[a-z0-9-]+$"


def _project_out(row) -> Project:
    skills = [s.strip() for s in (row["skills"] or "").split(",") if s.strip()]
    return Project(
        slug=row["slug"],
        title=row["name"],
        summary=row["summary"],
        status=STATUS_TO_CONTRACT.get(row["status"], "active"),
        skills=skills,
        attribution=row["attribution"],
    )


def _knowledge_out(row) -> KnowledgeEntry:
    try:
        tags = json.loads(row["tags"]) if row["tags"] else []
    except (ValueError, TypeError):
        tags = []
    return KnowledgeEntry(
        title=row["title"],
        kind=row["kind"],
        body=row["summary"],
        tags=tags,
        verification=row["verification"] or "untested",
        source_url=row["source_url"],
        checked_at=row["checked_at"],
    )


# ---------------------------------------------------------------- projects
@router.get("/projects", response_model=list[Project])
def list_projects_contract(skill: str | None = None,
                           status: ContractStatus | None = None):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY is_hero DESC, status, name"
        ).fetchall()
    out = [_project_out(r) for r in rows]
    if status is not None:
        out = [p for p in out if p.status == status]
    if skill is not None:
        wanted = skill.strip().lower()
        out = [p for p in out
               if wanted in [s.lower() for s in p.skills]]
    return out


@router.get("/projects/{slug}", response_model=ProjectDetail)
def get_project_contract(slug: str = Path(pattern=SLUG_PATTERN)):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            raise HTTPException(404, "project not found")
        evidence = rows_to_dicts(conn.execute(
            "SELECT type, url, note, recorded_at FROM evidence "
            "WHERE project_slug = ? ORDER BY recorded_at, id",
            (slug,)).fetchall())
        metrics = rows_to_dicts(conn.execute(
            "SELECT name, baseline, result, method, run_command, "
            "environment, pass_fail_criteria, declared_failing_cases, "
            "run_at FROM metric_runs WHERE project_slug = ? "
            "ORDER BY run_at, id", (slug,)).fetchall())
    base = _project_out(row)
    return ProjectDetail(**base.model_dump(), evidence=evidence,
                         metrics=metrics)


# ---------------------------------------------------------------- knowledge
@router.get("/knowledge", response_model=list[KnowledgeEntry])
def list_knowledge(q: str | None = None,
                   label: VerificationLabel | None = None):
    sql = "SELECT * FROM vault_entries WHERE 1=1"
    args = []
    if q:
        sql += (" AND (title LIKE ? OR summary LIKE ? OR category LIKE ? "
                "OR program LIKE ?)")
        like = f"%{q}%"
        args += [like, like, like, like]
    if label is not None:
        sql += " AND verification = ?"
        args.append(label)
    sql += " ORDER BY kind, COALESCE(amount_usd, 0) DESC, title"
    with connect() as conn:
        rows = conn.execute(sql, args).fetchall()
    return [_knowledge_out(r) for r in rows]


@router.post("/knowledge", response_model=KnowledgeEntry, status_code=201)
def create_knowledge(entry: KnowledgeEntryIn):
    verified = 0 if entry.verification == "untested" else 1
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO vault_entries (kind, title, category, program, "
            "summary, amount_usd, source_url, verified, checked_at, "
            "verification, tags) VALUES (?, ?, NULL, NULL, ?, NULL, ?, ?, "
            "?, ?, ?)",
            (entry.kind, entry.title, entry.body, entry.source_url,
             verified, entry.checked_at.isoformat(), entry.verification,
             json.dumps(entry.tags)))
        conn.commit()
        row = conn.execute("SELECT * FROM vault_entries WHERE id = ?",
                           (cur.lastrowid,)).fetchone()
    return _knowledge_out(row)


# ------------------------------------------------------------------- ledger
@router.get("/ledger", response_model=list[LedgerEntry])
def list_run_ledger(project: str | None = None):
    sql = "SELECT * FROM run_ledger WHERE 1=1"
    args = []
    if project is not None:
        sql += " AND project_slug = ?"
        args.append(project)
    sql += " ORDER BY ran_at, id"
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, args).fetchall())


@router.post("/ledger", response_model=LedgerEntry, status_code=201)
def create_run_ledger(entry: LedgerEntryIn):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO run_ledger (project_slug, action, result, "
            "run_command, evidence_url, ran_at) VALUES (?, ?, ?, ?, ?, ?)",
            (entry.project_slug, entry.action, entry.result,
             entry.run_command, entry.evidence_url,
             entry.ran_at.isoformat()))
        conn.commit()
        row = conn.execute("SELECT * FROM run_ledger WHERE id = ?",
                           (cur.lastrowid,)).fetchone()
    return dict(row)


# ------------------------------------------------------------------ reviews
@router.post("/reviews", response_model=ReviewRecord, status_code=201)
def create_review(record: ReviewRecordIn):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO reviews (subject, reviewer, decision, reason, "
            "reviewed_at) VALUES (?, ?, ?, ?, ?)",
            (record.subject, record.reviewer, record.decision,
             record.reason, record.reviewed_at.isoformat()))
        conn.commit()
        row = conn.execute("SELECT * FROM reviews WHERE id = ?",
                           (cur.lastrowid,)).fetchone()
    return dict(row)
