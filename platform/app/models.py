"""Pydantic models for the v1.1 contract surface (Instinct's platform
contract, canonical copy: Tawffik/knowledge-platform `contract/openapi.yaml`).

These mirror the contract schemas field-for-field. FastAPI/Pydantic
validation failures return 422 natively, which is exactly what the
contract's negative test suite requires (400/422, never 404/405/200).
"""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

VerificationLabel = Literal["tested", "documented", "untested"]
ContractStatus = Literal["active", "archived", "wip"]
EvidenceType = Literal["commit", "test-output", "video", "metric", "doc"]
ContractKnowledgeKind = Literal["writeup", "cheatsheet", "tool-note", "research"]
# Read side only: the local vault also holds payouts and tips, which the
# contract's kind enum does not cover. They are exposed as a declared
# local extension on GET /knowledge (see V1.1-REPORT.md); the write side
# (KnowledgeEntryIn) accepts the contract kinds only.
KnowledgeKindOut = Literal[
    "writeup", "cheatsheet", "tool-note", "research", "payout", "tip"]
RunResult = Literal["pass", "fail", "blocked"]
Reviewer = Literal["instinct", "elkaref"]
ReviewDecision = Literal["accepted", "rejected", "accepted-with-notes"]


class Evidence(BaseModel):
    type: EvidenceType
    url: str
    note: str | None = None
    recorded_at: date


class MetricRun(BaseModel):
    name: str
    baseline: str
    result: str
    method: str
    run_command: str
    environment: str | None = None
    pass_fail_criteria: str
    declared_failing_cases: str
    run_at: datetime


class Project(BaseModel):
    slug: str
    title: str
    summary: str | None = None
    status: ContractStatus
    skills: list[str]
    attribution: str | None = None


class ProjectDetail(Project):
    evidence: list[Evidence] = []
    metrics: list[MetricRun] = []


class KnowledgeEntryIn(BaseModel):
    title: str
    kind: ContractKnowledgeKind
    body: str | None = None
    tags: list[str] = []
    verification: VerificationLabel
    source_url: str
    checked_at: date


class KnowledgeEntry(BaseModel):
    title: str
    kind: KnowledgeKindOut
    body: str | None = None
    tags: list[str] = []
    verification: VerificationLabel
    source_url: str | None = None
    checked_at: date | None = None


class LedgerEntryIn(BaseModel):
    """Contract LedgerEntry(In): a lab *run log* entry — not the local
    bounty-outcome ledger (see app/db.py run_ledger note)."""
    project_slug: str
    action: str
    result: RunResult
    run_command: str
    evidence_url: str | None = None
    ran_at: datetime


class LedgerEntry(LedgerEntryIn):
    id: int


class ReviewRecordIn(BaseModel):
    subject: str
    reviewer: Reviewer
    decision: ReviewDecision
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def _reason_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason must not be blank")
        return v

    reviewed_at: datetime


class ReviewRecord(ReviewRecordIn):
    id: int
