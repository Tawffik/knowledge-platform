# Nx01 Platform v1 × Instinct Platform Contract — Gap Report

**Date:** 2026-11-26 · **Method:** contract files read from `Tawffik/security-youtube-channel-plan` → `coordination/platform/contract/` (`openapi.yaml`, `test_contract_negative.py`, `test_schema_offline.py`, `README.md`); local platform started (`uvicorn app.main:app`, port 8000), probed live, and Instinct's pytest suite run against it. No platform code was modified.

## ⚠️ Read this first — the contract copy is already archived

The contract README now carries a banner dated **2026-11-26**: the canonical home of the knowledge platform moved to a private repo **`knowledge-platform`** (owner-approved reorganisation), and the copy in the channel-plan repo is a **historical archive — no longer updated**. This reconciliation is therefore against the archived draft. Before v1.1 work starts, confirm which contract is canonical: this draft, or the `knowledge-platform` version.

## Headline result

| Measure | Result |
|---|---|
| Contract paths | 5 paths / 7 operations — **2 conceptually present (under `/api` prefix, different shapes), 3 operations missing entirely (all POSTs), 2 present-but-different-entity (ledger)** |
| Contract schemas | 10 — **0 fully conformant**, 2 partial (Project, KnowledgeEntry), 8 missing |
| Instinct's negative suite vs local server | **2 passed / 6 failed / 0 skipped** (details below) |
| Instinct's offline schema tests (contract self-consistency) | **9/9 passed** — the YAML itself is sound; the gaps are all on the local side |
| False accepts | **None.** Every test failure is a *missing surface* failure (404/405/HTML page), never the server accepting invalid data — the local API is read-only, so it cannot wrongly accept anything |

## Paths — per-item verdicts

| # | Contract operation | Local equivalent | Verdict | Notes |
|---|---|---|---|---|
| 1 | `GET /projects` (params: `skill`, `status` ∈ active/archived/wip) | `GET /api/projects` | **Shape mismatch** | Path prefix differs (`/api`). Worse: `GET /projects` locally returns the **HTML projects page** (200, text/html) — a live collision with the contract path. `status` enum mismatch: local `live\|proposed` vs contract `active\|archived\|wip`. Contract's `skill` filter missing (local has `hero` instead). |
| 2 | `GET /projects/{slug}` → ProjectDetail | `GET /api/projects/{slug}` | **Shape mismatch** | Exists and 404s correctly for unknown slugs, but returns the flat local project row — no `evidence`/`metrics` (see ProjectDetail below). Slug pattern `^[a-z0-9-]+$` not enforced (any string → DB lookup → 404). |
| 3 | `GET /knowledge` (params: `q`, `label`) | `GET /api/vault` | **Shape mismatch** | Same concept (the Intel Vault), different name, params and item shape. Local params: `kind`, `category`, `q`, `limit`, `offset`. No `label` (verification) filter. |
| 4 | `POST /knowledge` → 201 / 422 | — | **Missing** | Local API is read-only; no POST anywhere. Returns 404. |
| 5 | `GET /ledger` (param: `project`) | `GET /api/ledger` | **Different entity** | Same word, different domain object. Contract ledger = *lab run log* (project_slug, action, result, run_command, ran_at). Local ledger = *Zero Track Lab bounty-outcome ledger* (candidate_id, gate_verdict, program_verdict, bounty…). Neither is a superset of the other. Local params: `gate_verdict`, `include_examples`. |
| 6 | `POST /ledger` → 201 / 422 | — | **Missing** | Returns **405** locally (the HTML page route `/ledger` exists for GET, so POST is method-rejected rather than not-found). |
| 7 | `POST /reviews` → 201 / 422 | — | **Missing** | No reviews concept anywhere in the local platform. Returns 404. |

**Local-only extras (not in the contract, no conflict):** `GET /api/stats`, `GET /api/vault/categories`, `GET /api/vault/{entry_id}`, `GET /api/ledger/metrics`.

## Schemas — per-item verdicts

| # | Schema | Verdict | Detail |
|---|---|---|---|
| 1 | `VerificationLabel` (enum: tested / documented / untested) | **Missing** | Local vault has `verified` as INTEGER 0/1 — coarser, and cannot express *documented* vs *tested*. No enum enforcement. |
| 2 | `Evidence` (required: type ∈ commit/test-output/video/metric/doc, url, recorded_at) | **Missing** | No evidence objects anywhere. Nearest fragments: `vault_entries.source_url`, `projects.repo_url` — neither is a typed, dated Evidence record attached to a project. |
| 3 | `MetricRun` (8 required: name, baseline, result, method, run_command, pass_fail_criteria, declared_failing_cases, run_at) | **Missing** | Local `metrics` table is a monthly aggregate (`month, name, value, numerator, denominator, notes`) — a different concept. None of the reproducibility fields (run_command, method, criteria, declared failing cases) exist. `GET /api/ledger/metrics` currently returns `[]`. |
| 4 | `Project` (required: slug, title, status, skills[]) | **Partial / shape mismatch** | `slug` ✓, `summary` ✓. `title` ✗ — local field is `name` (plus an extra `tagline`). `status` enum mismatch (live/proposed vs active/archived/wip). `skills` shape mismatch — local is one comma-separated **string** (`"Python,GitHub Actions"`), contract wants an **array of strings**. Extras locally: `id`, `is_hero`, `visibility`, `repo_url`, `note`. |
| 5 | `attribution` (field on Project) | **Missing as a field** | The information partially exists as free text in the project `note` field (e.g. the Agentic-Bug-Hunter fork-attribution note), but there is no dedicated `attribution` field, so it is neither queryable nor guaranteed present. Contract marks it a first-class honesty field; locally it is incidental prose. |
| 6 | `ProjectDetail` (Project + evidence[] + metrics[]) | **Missing** | Detail endpoint returns the flat row only; no evidence or metric arrays exist to attach. |
| 7 | `KnowledgeEntry` (required: title, kind, verification, source_url, checked_at) | **Partial / shape mismatch** | Local `vault_entries`: `title` ✓, `source_url` ✓. `checked_at` ✗ missing. `verification` ✗ (see #1). `kind` enum mismatch — local: payout/writeup/tip/research; contract: writeup/cheatsheet/tool-note/research (only *writeup* and *research* overlap; payouts and tips have no contract counterpart — the contract's "knowledge" is narrower than the vault). `body` ✗ (local has `summary`); `tags` ✗. Local extras: `program`, `amount_usd`, `category`. |
| 8 | `KnowledgeEntryIn` | **Missing** | No write endpoint (see path #4). |
| 9 | `LedgerEntry` / `LedgerEntryIn` | **Missing** | Local ledger is the bounty-outcome ledger, not the contract's run log (see path #5). No `run_command` field exists anywhere locally — the contract's core reproducibility requirement has no local home. |
| 10 | `ReviewRecordIn` (required: subject, reviewer ∈ instinct/elkaref, decision ∈ accepted/rejected/accepted-with-notes, **reason**, reviewed_at) | **Missing** | No reviews table, endpoint, or concept in the local platform. The mutual-review workflow currently lives only in email/repo coordination files. |

## SkillTag — resolved

The current contract README states it explicitly: in MVP scope, skills are a **plain array of string tags directly on Project — there is no standalone SkillTag schema**, and the YAML confirms it (10 schemas, none named SkillTag). The earlier coordination note ("README names SkillTag but the contract has no such schema") referred to the superseded first version of the README; the corrected version settles the question. **No action needed** beyond storing local skills as an array (see fix 3).

## Test run — Instinct's suite against the local server

`BASE_URL=http://127.0.0.1:8000 python -m pytest test_contract_negative.py -v` → **2 passed, 6 failed, 0 skipped**.

| Test | Result | Actual local behaviour |
|---|---|---|
| knowledge entry without source rejected | ❌ FAIL | `POST /knowledge` → **404** (endpoint absent; test requires 400/422) |
| knowledge invalid verification label rejected | ❌ FAIL | `POST /knowledge` → **404** |
| ledger entry without run_command rejected | ❌ FAIL | `POST /ledger` → **405** (HTML page route) |
| review without reason rejected | ❌ FAIL | `POST /reviews` → **404** |
| review invalid decision rejected | ❌ FAIL | `POST /reviews` → **404** |
| project slug pattern enforced | ✅ PASS | `GET /projects/Bad_Slug!` → 404, which the test accepts (400/404/422) — passes via not-found, **not** via pattern validation |
| projects list shape | ❌ FAIL | `GET /projects` → 200 **HTML page**; `r.json()` raises JSONDecodeError |
| openapi docs exposed | ✅ PASS | `GET /openapi.json` → 200 (FastAPI native) |

**Skip behaviour (as designed):** the suite module-skips all 8 tests when no server answers on `BASE_URL` — Instinct's README records exactly that on 2026-11-25 (8 skipped / 0 passed / 0 failed). With the server up there were 0 skips, so the 2/8 above is a true measurement, not a skip artefact.

**Reading of the failures:** all six are *absence* failures. The local platform never accepted invalid input — it has no input surface at all. The gap is therefore "the contract's write + evidence surface is unimplemented", not "v1 validates badly".

**Environment caveat for reruns in this VM:** httpx 0.28 crashes at import/collection (`InvalidURL: Invalid port: ':1]'`) on the runtime's lowercase `no_proxy` value (it contains bracketed IPv6 entries). Run the suite with `no_proxy`/`NO_PROXY` overridden to `127.0.0.1` and the `*_PROXY` vars unset, as was done here.

## Fix suggestions for v1.1 (concrete, ordered)

1. **Settle the canonical contract first.** The repo copy is archived in favour of `knowledge-platform` (README banner, 2026-11-26). Get Instinct's current contract from there (or his confirmation that this draft still stands) before building against it — otherwise v1.1 may reconcile against a superseded draft.
2. **Resolve the path collision.** Decide one scheme: contract paths at root (`/projects`, `/knowledge`, `/ledger`, `/reviews`) with the HTML pages moved (e.g. under `/ui/…`), or keep `/api/…` and have Instinct amend the contract. The current state — `GET /projects` serving HTML — actively breaks his list-shape test and would break any contract client.
3. **Adopt Pydantic response models matching the schemas.** Concretely: rename/alias `name`→`title`; convert `skills` from CSV string to a JSON array (split on seed + store as JSON); map status `live→active`, `proposed→wip`, add `archived`; add the `skill` query filter to the projects list.
4. **Add a dedicated `attribution` column** to `projects`, seeded from the existing free-text notes (Agentic-Bug-Hunter fork note first), and expose it in both list and detail responses.
5. **Add `evidence` and `metric_runs` tables** (project-linked), implementing `Evidence` and `MetricRun` field-for-field — including `run_command`, `pass_fail_criteria` and `declared_failing_cases` — and return them from the project detail endpoint (`ProjectDetail`). Keep the existing monthly `metrics` aggregates as a separate, clearly-named concept.
6. **Align the vault with `KnowledgeEntry`:** add `checked_at` (seed = vault verification date), replace the `verified` 0/1 flag with the `VerificationLabel` enum (interim mapping: verified payouts/writeups → `documented`; only hands-on-tested items → `tested`), and document the `kind` mapping — contract kinds (cheatsheet, tool-note) vs local kinds (payout, tip): either extend the contract enum or keep payouts/tips as a declared local extension.
7. **Implement the write surface with FastAPI validation** (which yields 422 natively, satisfying the negative tests): `POST /knowledge` (source_url + checked_at required), `POST /reviews` (reason required, decision/reviewer enums). For `POST /ledger`, first resolve the entity clash in #8.
8. **Resolve the ledger name clash explicitly.** The contract's run-log and the local bounty-outcome ledger are both legitimate but different. Rename one — e.g. contract run log at `/runs`, bounty ledger stays `/ledger` — and have both parties amend their documents so "ledger" means one thing.
9. **Enforce the slug pattern** on the path parameter (`Path(pattern="^[a-z0-9-]+$")`) so invalid slugs are rejected by validation (422) rather than incidentally 404ing.
10. **Acceptance gate for v1.1:** Instinct's suite at **8/8 passed** against a locally running server (with the no_proxy workaround noted above), plus his offline schema suite kept at 9/9 if the YAML changes.

*Report only — no platform code, contract files, or GitHub content were modified. Server started for testing was stopped afterwards.*
