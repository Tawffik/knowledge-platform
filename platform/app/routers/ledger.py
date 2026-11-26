from fastapi import APIRouter, Query

from app.db import connect, rows_to_dicts

router = APIRouter(prefix="/api/ledger", tags=["ledger"])


@router.get("")
def list_ledger(gate_verdict: str | None = Query(
        None, pattern="^(pass|reject)$"),
                include_examples: bool = True):
    sql = "SELECT * FROM ledger_entries WHERE 1=1"
    args = []
    if gate_verdict:
        sql += " AND gate_verdict = ?"
        args.append(gate_verdict)
    if not include_examples:
        sql += " AND is_example = 0"
    sql += " ORDER BY recorded_at"
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, args).fetchall())


@router.get("/metrics")
def list_metrics(month: str | None = None):
    sql = "SELECT * FROM metrics WHERE 1=1"
    args = []
    if month:
        sql += " AND month = ?"
        args.append(month)
    sql += " ORDER BY month, name"
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, args).fetchall())
