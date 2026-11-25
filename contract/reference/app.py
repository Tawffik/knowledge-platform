"""
تطبيق مرجعي محلي لعقد المنصة (تنفيذ Instinct المرجعي، ليس تسليم الكارِف).

الغرض: تشغيل جناح القبول (test_contract_negative.py) ضد خادم حقيقي محلي
لإثبات أن العقد قابل للتنفيذ كما هو مكتوب، وتوفير أساس مقارنة ملموس
لمراجعة نسخة الكارِف عند تسليمها.

محلي مجاني بالكامل: FastAPI + SQLite، بلا حسابات ولا استضافة.
تشغيل: uvicorn app:app --port 8000
"""
import sqlite3
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field, HttpUrl

DB = "/tmp/platform-ref.db"


def init_db():
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS projects(
        slug TEXT PRIMARY KEY, title TEXT NOT NULL, summary TEXT,
        status TEXT NOT NULL, skills TEXT NOT NULL, attribution TEXT);
    CREATE TABLE IF NOT EXISTS knowledge(
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        kind TEXT NOT NULL, body TEXT, tags TEXT, verification TEXT NOT NULL,
        source_url TEXT NOT NULL UNIQUE, checked_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ledger(
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_slug TEXT NOT NULL,
        action TEXT NOT NULL, result TEXT NOT NULL, run_command TEXT NOT NULL,
        evidence_url TEXT, ran_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL,
        reviewer TEXT NOT NULL, decision TEXT NOT NULL, reason TEXT NOT NULL,
        reviewed_at TEXT NOT NULL);
    """)
    con.commit()
    con.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    con = sqlite3.connect(DB)
    if not con.execute("SELECT 1 FROM projects LIMIT 1").fetchone():
        con.execute(
            "INSERT INTO projects VALUES(?,?,?,?,?,?)",
            ("vulnradar", "VulnRadar", "ماسح ثغرات تعليمي", "wip",
             '["python","osint"]', "أصلي"))
        con.commit()
    con.close()
    yield


app = FastAPI(title="Portfolio Platform API (reference)", version="0.1.0-draft",
              lifespan=lifespan)

# --- نماذج مطابقة لسكيمات العقد ---

VerificationLabel = Literal["tested", "documented", "untested"]


class Project(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str
    summary: Optional[str] = None
    status: Literal["active", "archived", "wip"]
    skills: list[str]
    attribution: Optional[str] = None


class KnowledgeEntry(BaseModel):
    title: str
    kind: Literal["writeup", "cheatsheet", "tool-note", "research"]
    body: Optional[str] = None
    tags: Optional[list[str]] = None
    verification: VerificationLabel
    source_url: HttpUrl
    checked_at: date


class LedgerEntry(BaseModel):
    project_slug: str
    action: str
    result: Literal["pass", "fail", "blocked"]
    run_command: str
    evidence_url: Optional[HttpUrl] = None
    ran_at: datetime


class ReviewRecordIn(BaseModel):
    subject: str
    reviewer: Literal["instinct", "elkaref"]
    decision: Literal["accepted", "rejected", "accepted-with-notes"]
    reason: str = Field(min_length=1)
    reviewed_at: datetime


# --- المسارات ---

@app.get("/projects", response_model=list[Project])
def list_projects(skill: Optional[str] = None,
                  status: Optional[Literal["active", "archived", "wip"]] = None):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT slug,title,summary,status,skills,attribution FROM projects").fetchall()
    con.close()
    import json
    out = [Project(slug=r[0], title=r[1], summary=r[2], status=r[3],
                   skills=json.loads(r[4]), attribution=r[5]) for r in rows]
    if skill:
        out = [p for p in out if skill in p.skills]
    if status:
        out = [p for p in out if p.status == status]
    return out


@app.get("/projects/{slug}", response_model=Project)
def get_project(slug: str = Path(pattern=r"^[a-z0-9-]+$")):
    con = sqlite3.connect(DB)
    r = con.execute(
        "SELECT slug,title,summary,status,skills,attribution FROM projects WHERE slug=?",
        (slug,)).fetchone()
    con.close()
    if not r:
        raise HTTPException(404, "غير موجود")
    import json
    return Project(slug=r[0], title=r[1], summary=r[2], status=r[3],
                   skills=json.loads(r[4]), attribution=r[5])


@app.get("/knowledge")
def list_knowledge(q: Optional[str] = None, label: Optional[VerificationLabel] = None):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT title,kind,body,tags,verification,source_url,checked_at FROM knowledge").fetchall()
    con.close()
    keys = ("title", "kind", "body", "tags", "verification", "source_url", "checked_at")
    out = [dict(zip(keys, r)) for r in rows]
    if q:
        out = [e for e in out if q in (e["title"] or "")]
    if label:
        out = [e for e in out if e["verification"] == label]
    return out


@app.post("/knowledge", status_code=201)
def add_knowledge(entry: KnowledgeEntry):
    con = sqlite3.connect(DB)
    import json
    try:
        con.execute(
            "INSERT INTO knowledge(title,kind,body,tags,verification,source_url,checked_at) VALUES(?,?,?,?,?,?,?)",
            (entry.title, entry.kind, entry.body,
             json.dumps(entry.tags) if entry.tags else None,
             entry.verification, str(entry.source_url), entry.checked_at.isoformat()))
        con.commit()
    except sqlite3.IntegrityError:
        con.close()
        raise HTTPException(409, "مصدر مكرر")
    con.close()
    return {"created": True}


@app.get("/ledger")
def list_ledger(project: Optional[str] = None):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT project_slug,action,result,run_command,evidence_url,ran_at FROM ledger").fetchall()
    con.close()
    keys = ("project_slug", "action", "result", "run_command", "evidence_url", "ran_at")
    out = [dict(zip(keys, r)) for r in rows]
    if project:
        out = [e for e in out if e["project_slug"] == project]
    return out


@app.post("/ledger", status_code=201)
def add_ledger(entry: LedgerEntry):
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO ledger(project_slug,action,result,run_command,evidence_url,ran_at) VALUES(?,?,?,?,?,?)",
        (entry.project_slug, entry.action, entry.result, entry.run_command,
         str(entry.evidence_url) if entry.evidence_url else None,
         entry.ran_at.isoformat()))
    con.commit()
    con.close()
    return {"created": True}


@app.post("/reviews", status_code=201)
def add_review(review: ReviewRecordIn):
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO reviews(subject,reviewer,decision,reason,reviewed_at) VALUES(?,?,?,?,?)",
        (review.subject, review.reviewer, review.decision, review.reason,
         review.reviewed_at.isoformat()))
    con.commit()
    con.close()
    return {"created": True}
