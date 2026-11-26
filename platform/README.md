# Nx01 Platform — Zero Track Sec

**The public face of an operating security lab — not a static portfolio.**

A full-stack, API-first platform that hosts the owner's projects as living
products:

- **Projects** — every card is live data from the database via the REST API
  (hero projects, live vs *proposed* honestly labelled, private repos flagged).
- **Bug Bounty Intel Vault** — verified payouts, real writeups, attributed
  tips and research, fully searchable/filterable through the API. Every entry
  carries its source URL; unverified figures are *not* in this database (they
  stay quarantined in the vault's leads file).
- **Zero Track Lab Ledger** — the append-only public outcome record of the
  lab: gate passes **and gate rejects with reasons**, program verdicts,
  severities, bounties and run costs. Entries from the ledger template are
  flagged `is_example` until real operation starts.
- **Monthly lab metrics** — table + API ready for the lab's published metrics.

## Stack (zero budget — free/local only)

| Layer    | Tech                                   | Cost |
|----------|----------------------------------------|------|
| Backend  | Python 3.12 + FastAPI + Uvicorn        | free |
| Database | SQLite (stdlib `sqlite3`, file-based)  | free |
| Frontend | Server-delivered HTML + vanilla JS, no build step | free |
| Hosting  | Local / free tier only (see below)     | free |

No paid services, no paid hosting assumptions, no domains. **Zero budget is a
hard constraint from the owner** — everything below stays inside free tiers.

## Run it

```bash
cd ~/workspace/nx01-platform
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m app.seed          # builds data/platform.db from source files
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open:

- Home:      http://127.0.0.1:8000/
- Projects:  http://127.0.0.1:8000/projects
- Vault:     http://127.0.0.1:8000/vault
- Ledger:    http://127.0.0.1:8000/ledger
- API docs:  http://127.0.0.1:8000/docs  (FastAPI Swagger UI)

## API

| Endpoint | Description |
|---|---|
| `GET /api/stats` | Live counters (projects, vault by kind, verified payout total, ledger) |
| `GET /api/projects?status=live\|proposed&hero=true` | Project list |
| `GET /api/projects/{slug}` | Project detail |
| `GET /api/vault?kind=payout\|writeup\|tip\|research&category=&q=&limit=&offset=` | Vault browser/search |
| `GET /api/vault/categories?kind=` | Vault category facets with counts |
| `GET /api/vault/{id}` | Single vault entry |
| `GET /api/ledger?gate_verdict=pass\|reject&include_examples=false` | Lab ledger (rejects included by design) |
| `GET /api/ledger/metrics?month=YYYY-MM` | Monthly lab metrics |

### Contract surface (v1.1 — Instinct's platform contract, root paths)

Canonical contract: `Tawffik/knowledge-platform` → `contract/openapi.yaml`.
Implemented in `app/routers/contract_api.py` + `app/models.py`; details and
verification results in `V1.1-REPORT.md`.

| Endpoint | Description |
|---|---|
| `GET /projects?skill=&status=active\|archived\|wip` | Contract Project list (title, skills array, attribution) |
| `GET /projects/{slug}` | ProjectDetail — Project + `evidence[]` + `metrics[]` (MetricRun) |
| `GET /knowledge?q=&label=tested\|documented\|untested` | Vault as KnowledgeEntry (verification label, source, checked_at) |
| `POST /knowledge` → 201 | Add a knowledge entry (source_url + checked_at required, else 422) |
| `GET /ledger?project=` | Contract ledger = lab **run log** (run_command mandatory) |
| `POST /ledger` → 201 | Record a run |
| `POST /reviews` → 201 | Record a mutual review (reason required, else 422) |

**Naming note:** the contract's `/ledger` (run log) and the v1
`/api/ledger` (Zero Track Lab bounty-outcome ledger) are different
entities that share a word. Both keep their homes; neither was renamed.
The HTML pages moved to `/ui/projects` and `/ui/ledger` so the bare paths
can serve the contract JSON.

## Where the data comes from (reproducible seed)

`app/seed.py` rebuilds the DB from the owner's real local files — re-run it
any time those files change:

- Projects: curated list grounded in
  `~/workspace/your_files/projects-and-portfolio-plan.md`
  (audit of the owner's GitHub: BugBountyCI, VulnRadar, CyberOS/My-app-,
  security-research-agent, Agentic-Bug-Hunter, llm-security-guard, … plus the
  plan's proposed projects, marked `proposed`).
- Vault: parsed from `~/workspace/bug-bounty-intel-vault/`
  (`payouts/notable-payouts.md` — verified only — `writeups/INDEX.md`,
  `tips/TIPS-AND-TRICKS.md`, `research/INDEX.md`).
- Ledger: `~/workspace/zero-track-lab/ledger/ledger-template.jsonl`,
  loaded with `is_example = 1`.

## Free deployment path (when the owner decides to publish)

Still zero budget — pick one when the time comes:

1. **GitHub Pages (static export)** — free. Add a small export script that
   dumps `/api/*` responses to JSON and renders the four pages statically;
   the frontend already treats the API as its only data source, so this is a
   mechanical change. Loses live server search (client-side filter instead).
2. **Free-tier app host** — e.g. a free Python web-service tier (Render /
   Fly.io / PythonAnywhere free tiers, as available) running the exact
   `uvicorn` command above with the seeded SQLite file. Keeps the live API.
   Free tiers sleep/cold-start; acceptable for a portfolio-grade platform.
3. **Home/local hosting** — run it on the owner's own machine/VPS he already
   has, behind a free tunnel (e.g. Cloudflare Tunnel free tier). $0, full API.

No option requires a domain: all of the above work on the provider's free
subdomain.

## Structure

```
nx01-platform/
├── README.md
├── requirements.txt
├── app/
│   ├── main.py            # FastAPI app, page routes, static mount
│   ├── db.py              # SQLite schema + connection
│   ├── seed.py            # reproducible seed from local source files
│   └── routers/
│       ├── projects.py    # /api/projects
│       ├── vault.py       # /api/vault (+ categories)
│       ├── ledger.py      # /api/ledger (+ metrics)
│       └── stats.py       # /api/stats
├── static/                # index / projects / vault / ledger + css/js
└── data/platform.db       # generated by the seed (not source)
```

## v1 limitations / v2 ideas

- Read-only API (no auth, no admin write endpoints yet).
- Seed parsers are regex-based against the vault's current Markdown formats;
  if the vault format changes, update `app/seed.py` parsers.
- Metrics table ships empty — it fills when the Lab's first real month runs.
- v2: static export script for GitHub Pages, project detail pages per slug,
  ledger write path fed by the Lab pipeline (append-only, signed entries),
  RSS/JSON feeds for the vault.
