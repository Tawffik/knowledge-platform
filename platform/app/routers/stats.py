from fastapi import APIRouter

from app.db import connect

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def stats():
    with connect() as conn:
        def one(sql, args=()):
            row = conn.execute(sql, args).fetchone()
            return row[0] if row and row[0] is not None else 0

        return {
            "projects_total": one("SELECT COUNT(*) FROM projects"),
            "projects_live": one(
                "SELECT COUNT(*) FROM projects WHERE status = 'live'"),
            "projects_proposed": one(
                "SELECT COUNT(*) FROM projects WHERE status = 'proposed'"),
            "vault_entries": one("SELECT COUNT(*) FROM vault_entries"),
            "vault_by_kind": {
                r[0]: r[1] for r in conn.execute(
                    "SELECT kind, COUNT(*) FROM vault_entries GROUP BY kind")
            },
            "verified_payouts_total_usd": one(
                "SELECT COALESCE(SUM(amount_usd), 0) FROM vault_entries "
                "WHERE kind = 'payout' AND verified = 1"),
            "ledger_entries": one("SELECT COUNT(*) FROM ledger_entries"),
            "ledger_gate_rejects": one(
                "SELECT COUNT(*) FROM ledger_entries WHERE gate_verdict = 'reject'"),
            "ledger_program_resolved": one(
                "SELECT COUNT(*) FROM ledger_entries "
                "WHERE program_verdict = 'resolved'"),
        }
