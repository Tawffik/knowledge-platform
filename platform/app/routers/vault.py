from fastapi import APIRouter, HTTPException, Query

from app.db import connect, rows_to_dicts

router = APIRouter(prefix="/api/vault", tags=["vault"])
KINDS = "^(payout|writeup|tip|research)$"


@router.get("")
def list_vault(kind: str | None = Query(None, pattern=KINDS),
               category: str | None = None,
               q: str | None = None,
               limit: int = Query(200, le=500),
               offset: int = 0):
    sql = "SELECT * FROM vault_entries WHERE 1=1"
    args = []
    if kind:
        sql += " AND kind = ?"
        args.append(kind)
    if category:
        sql += " AND category = ?"
        args.append(category)
    if q:
        sql += " AND (title LIKE ? OR summary LIKE ? OR category LIKE ? OR program LIKE ?)"
        like = f"%{q}%"
        args += [like, like, like, like]
    sql += " ORDER BY kind, COALESCE(amount_usd, 0) DESC, title LIMIT ? OFFSET ?"
    args += [limit, offset]
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, args).fetchall())


@router.get("/categories")
def vault_categories(kind: str | None = Query(None, pattern=KINDS)):
    sql = ("SELECT category, COUNT(*) AS n FROM vault_entries "
           "WHERE category IS NOT NULL")
    args = []
    if kind:
        sql += " AND kind = ?"
        args.append(kind)
    sql += " GROUP BY category ORDER BY n DESC, category"
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, args).fetchall())


@router.get("/{entry_id}")
def get_vault_entry(entry_id: int):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM vault_entries WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "vault entry not found")
    return dict(row)
