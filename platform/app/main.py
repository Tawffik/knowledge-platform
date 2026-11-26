"""Nx01 Platform — the public face of an operating security lab.

FastAPI backend (REST API + static frontend). Zero-budget stack:
Python + FastAPI + SQLite, no build step, no paid services.
"""
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import connect, init_schema
from app.routers import contract_api, ledger, projects, stats, vault

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="Nx01 Platform — Zero Track Sec",
    description="Projects, verified bug bounty intel vault, and the Zero Track "
                "Lab public results ledger. API-first; the frontend is a thin "
                "client of this API. v1.1 adds Instinct's contract surface at "
                "root paths (/projects, /knowledge, /ledger, /reviews): the "
                "contract /ledger is the lab run log, while the bounty-outcome "
                "ledger keeps its v1 home at /api/ledger (see V1.1-REPORT.md).",
    version="1.1.0",
)

app.include_router(projects.router)
app.include_router(vault.router)
app.include_router(ledger.router)
app.include_router(stats.router)
app.include_router(contract_api.router)


@app.on_event("startup")
def _startup():
    with connect() as conn:
        init_schema(conn)


def _page(name):
    return FileResponse(os.path.join(STATIC_DIR, name))


@app.get("/", include_in_schema=False)
def home():
    return _page("index.html")


# HTML pages live under /ui/… since v1.1: the bare /projects and /ledger
# paths belong to the contract API (they previously served these pages,
# which broke the contract's list endpoints — see CONTRACT-GAPS fix 2).
@app.get("/ui/projects", include_in_schema=False)
def projects_page():
    return _page("projects.html")


@app.get("/vault", include_in_schema=False)
def vault_page():
    return _page("vault.html")


@app.get("/ui/ledger", include_in_schema=False)
def ledger_page():
    return _page("ledger.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
