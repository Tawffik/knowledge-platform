from fastapi import APIRouter, HTTPException, Query

from app.db import connect, rows_to_dicts

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def list_projects(status: str | None = Query(None, pattern="^(live|proposed)$"),
                  hero: bool | None = None):
    sql = "SELECT * FROM projects WHERE 1=1"
    args = []
    if status:
        sql += " AND status = ?"
        args.append(status)
    if hero is not None:
        sql += " AND is_hero = ?"
        args.append(1 if hero else 0)
    sql += " ORDER BY is_hero DESC, status, name"
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, args).fetchall())


@router.get("/{slug}")
def get_project(slug: str):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
    if row is None:
        raise HTTPException(404, "project not found")
    return dict(row)
